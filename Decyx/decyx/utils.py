# utils.py

import re
import json
from ghidra.app.decompiler import DecompInterface, DecompileOptions
from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import VariableSizeException
from ghidra.app.services import DataTypeManagerService
from ghidra.program.model.listing import CodeUnit
from ghidra.program.model.pcode import HighFunctionDBUtil
from decyx.config import PROMPTS

# ---------------------------------------------------------------------------
# Data type helpers
# ---------------------------------------------------------------------------

def find_data_type_by_name(name, tool):
    service = tool.getService(DataTypeManagerService)
    data_type_managers = service.getDataTypeManagers()
    for manager in data_type_managers:
        data_type = manager.getDataType("/" + name)
        if data_type is None:
            data_type = manager.getDataType(name)
        if data_type is not None:
            return data_type
        all_data_types = manager.getAllDataTypes()
        for dt in all_data_types:
            if dt.getName().lower() == name.lower():
                return dt
    return None

# ---------------------------------------------------------------------------
# Low-level rename / retype helpers
# ---------------------------------------------------------------------------

def retype_variable(variable, new_type_name, tool):
    new_data_type = find_data_type_by_name(new_type_name, tool)
    if new_data_type is None:
        return False
    try:
        variable.setDataType(new_data_type, SourceType.USER_DEFINED)
        print("Successfully retyped variable '{}' to '{}'".format(variable.getName(), new_type_name))
        return True
    except VariableSizeException as e:
        print("Error: Variable size conflict when retyping '{}' to '{}'. Details: {}".format(
            variable.getName(), new_type_name, str(e)))
        return False
    except Exception as e:
        print("Error retyping variable '{}' to '{}': {}".format(
            variable.getName(), new_type_name, str(e)))
        return False

def retype_global_variable(listing, symbol, new_data_type):
    addr = symbol.getAddress()
    try:
        dt_len = max(1, new_data_type.getLength())
        block = listing.getProgram().getMemory().getBlock(addr)
        if block is None:
            print("Skipped retyping global variable '{}' at {} (no backing memory block).".format(
                symbol.getName(), addr))
            return

        available = int(block.getEnd().subtract(addr)) + 1
        if available < dt_len:
            print("Skipped retyping global variable '{}' at {} (need {} bytes, only {} available).".format(
                symbol.getName(), addr, dt_len, available))
            return

        listing.clearCodeUnits(addr, addr.add(dt_len - 1), False)
        data = listing.createData(addr, new_data_type)
        if data:
            print("Retyped global variable '{}' to '{}'".format(symbol.getName(), new_data_type.getName()))
        else:
            print("Error: Failed to create data for global variable '{}' with type '{}'".format(
                symbol.getName(), new_data_type.getName()))
    except Exception as e:
        print("Error retyping global variable '{}' to '{}': {}".format(
            symbol.getName(), new_data_type.getName(), str(e)))

def rename_function(func, new_name):
    func.setName(new_name, SourceType.USER_DEFINED)
    print("Renamed function to '{}'".format(new_name))

def rename_symbol(symbol, new_name):
    old_name = symbol.getName()
    symbol.setName(new_name, SourceType.USER_DEFINED)
    print("Renamed variable '{}' to '{}'".format(old_name, new_name))

# ---------------------------------------------------------------------------
# High-level apply helpers
# ---------------------------------------------------------------------------

def _get_high_function(func, current_program, monitor):
    """Re-decompiles func and returns the HighFunction. Returns None on failure."""
    decomp = DecompInterface()
    options = DecompileOptions()
    decomp.setOptions(options)
    decomp.toggleCCode(True)
    decomp.toggleSyntaxTree(True)
    decomp.openProgram(current_program)
    try:
        results = decomp.decompileFunction(func, 60, monitor)
        if results.decompileCompleted():
            return results.getHighFunction()
        print("Warning: re-decompilation failed while applying suggestions.")
        return None
    finally:
        decomp.dispose()

def _build_high_sym_map(high_func):
    """Returns a dict of { name -> HighSymbol } from the HighFunction's local symbol map."""
    sym_map = {}
    local_symbol_map = high_func.getLocalSymbolMap()
    symbols = local_symbol_map.getSymbols()
    while symbols.hasNext():
        sym = symbols.next()
        name = sym.getName()
        if name and not name.startswith("$$"):
            sym_map[name] = sym
    return sym_map

def _first_symbol(symbols):
    """Return first symbol from Java iterator/list-like containers."""
    if not symbols:
        return None
    if hasattr(symbols, "hasNext") and hasattr(symbols, "next"):
        return symbols.next() if symbols.hasNext() else None
    if hasattr(symbols, "iterator"):
        iterator = symbols.iterator()
        return iterator.next() if iterator.hasNext() else None
    if hasattr(symbols, "size") and hasattr(symbols, "get"):
        return symbols.get(0) if symbols.size() > 0 else None
    try:
        return symbols[0] if len(symbols) > 0 else None
    except Exception:
        pass
    try:
        return next(iter(symbols))
    except Exception:
        return None

def process_global_variable(symbol_table, listing, old_name, new_name, new_type_name, tool):
    """Process a global variable for renaming and retyping. Returns True if resolved."""
    names_to_try = [old_name]
    if old_name.startswith('_'):
        names_to_try.append(old_name[1:])
    else:
        names_to_try.append("_" + old_name)

    symbol = None
    for candidate in names_to_try:
        symbol = _first_symbol(symbol_table.getGlobalSymbols(candidate))
        if symbol is None:
            symbol = _first_symbol(symbol_table.getSymbols(candidate))
        if symbol is not None:
            break

    if symbol is None:
        return False

    if new_name:
        rename_symbol(symbol, new_name)
    if new_type_name:
        new_data_type = find_data_type_by_name(new_type_name, tool)
        if new_data_type:
            retype_global_variable(listing, symbol, new_data_type)
        else:
            print("Data type '{}' not found for global variable '{}'".format(
                new_type_name, symbol.getName()))
    return True

def apply_selected_suggestions(func, suggestions, selected, tool, monitor):
    """
    Applies the selected suggestions for renaming and retyping of variables and functions.

    All variable changes are batched inside a single Ghidra transaction. If changes
    are applied in separate transactions, each commit triggers a decompiler re-analysis
    that renumbers unnamed register temporaries - causing subsequent lookups by the
    original name to fail for the rest of the loop.
    """
    program = func.getProgram()
    listing = program.getListing()
    symbol_table = program.getSymbolTable()

    # Rename the function first (outside the variable transaction is fine)
    if selected['function_name']:
        rename_function(func, selected['function_name'])

    # Re-decompile once to get the HighFunction with the current (pre-change) symbol names
    high_func = _get_high_function(func, program, monitor)
    high_sym_map = _build_high_sym_map(high_func) if high_func is not None else {}

    # Database variables as fallback for any stack/parameter entries
    db_vars = list(func.getParameters()) + list(func.getLocalVariables())

    # Single transaction for all variable changes so the decompiler doesn't
    # re-analyse and renumber temporaries between individual updates
    transaction = program.startTransaction("Decyx: rename/retype variables")
    committed = False
    try:
        for i, var_suggestion in enumerate(selected['variables']):
            if not var_suggestion:
                continue

            old_name = suggestions['variables'][i]['old_name']
            new_name = var_suggestion.get('new_name', None)
            new_type_name = var_suggestion.get('new_type', None)

            # Common decompiler global naming prefixes
            if old_name.startswith(("DAT_", "_DAT_", "g_", "_g_")):
                process_global_variable(symbol_table, listing, old_name, new_name, new_type_name, tool)
                continue

            # Try HighSymbol first (covers all register-allocated temporaries)
            high_sym = high_sym_map.get(old_name)
            if high_sym is not None:
                resolved_name = new_name if new_name else old_name
                if new_type_name:
                    resolved_type = find_data_type_by_name(new_type_name, tool)
                    if resolved_type is None:
                        print("Data type '{}' not found for '{}', keeping existing type".format(new_type_name, old_name))
                        resolved_type = high_sym.getDataType()
                else:
                    resolved_type = high_sym.getDataType()
                try:
                    HighFunctionDBUtil.updateDBVariable(high_sym, resolved_name, resolved_type, SourceType.USER_DEFINED)
                    print("Updated (high) '{}' -> name='{}' type='{}'".format(old_name, resolved_name, resolved_type.getName()))
                    continue
                except Exception as e:
                    print("Error updating high symbol '{}': {} (trying database/global fallback)".format(old_name, e))

            # Fall back to database Variable (stack locals, parameters)
            var_obj = next((v for v in db_vars if v.getName() == old_name), None)
            if var_obj is not None:
                try:
                    if new_name:
                        rename_symbol(var_obj, new_name)
                    if new_type_name:
                        success = retype_variable(var_obj, new_type_name, tool)
                        if not success:
                            print("Warning: Failed to retype '{}' to '{}'".format(old_name, new_type_name))
                except Exception as e:
                    print("Error updating db variable '{}': {}".format(old_name, e))
                continue

            if process_global_variable(symbol_table, listing, old_name, new_name, new_type_name, tool):
                continue
            print("Variable '{}' not found (checked HighFunction + database + globals)".format(old_name))

        committed = True
    except Exception as e:
        print("Unexpected error during apply: {}".format(e))
    finally:
        program.endTransaction(transaction, committed)

    if committed:
        print("Finished applying suggestions.")
    else:
        print("Changes rolled back due to error.")
    return committed

# ---------------------------------------------------------------------------
# Comment / explanation helpers
# ---------------------------------------------------------------------------

def apply_line_comments(func, comments):
    program = func.getProgram()
    listing = program.getListing()
    for address_str, comment in comments.items():
        address = program.getAddressFactory().getAddress(address_str)
        if address is None:
            print("Warning: Invalid address {}".format(address_str))
            continue
        code_unit = listing.getCodeUnitAt(address)
        if code_unit:
            code_unit.setComment(CodeUnit.PRE_COMMENT, comment)
            print("Added PRE comment at address {}: {}".format(address_str, comment))
        else:
            print("Warning: No code unit found at address {}".format(address_str))
    print("Line comments applied.")

def apply_explanation(func, explanation):
    func.setComment(explanation)
    print("Added explanation as comment to the function.")

# ---------------------------------------------------------------------------
# Prompt preparation
# ---------------------------------------------------------------------------

def prepare_prompt(code, variables, action='rename_retype', callers_code=None, callees_code=None):
    prompt_template = PROMPTS.get(action)
    if not prompt_template:
        return None
    prompt = prompt_template
    if callers_code:
        prompt += "### Additional Context: Callers' Code\n"
        for caller_name, caller_code in callers_code.items():
            prompt += "#### Caller: {}\n\n{}\n\n\n".format(caller_name, caller_code)
    if callees_code:
        prompt += "### Additional Context: Callees' Code\n"
        for callee_name, callee_code in callees_code.items():
            prompt += "#### Callee: {}\n\n{}\n\n\n".format(callee_name, callee_code)
    prompt += "### Code:\n\n{}\n\n".format(code)
    if action != 'line_comments':
        prompt += "### Variables:\n\n{}\n\n".format(json.dumps(variables, indent=2))
    return prompt

# ---------------------------------------------------------------------------
# Type formatting helper
# ---------------------------------------------------------------------------

def format_new_type(type_str):
    fixed_type = re.sub(r'(?<!\s)\*', ' *', type_str)
    fixed_type = re.sub(r'\*\*+', lambda m: ' ' + ' *' * len(m.group()), fixed_type)
    fixed_type = re.sub(r'\s+', ' ', fixed_type).strip()
    return fixed_type
