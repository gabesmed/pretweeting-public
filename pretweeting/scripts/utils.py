def get_settings_file(dirpath, module_name):
  """
  Gets a settings file from the path
  """
  import ihooks, os
  loader = ihooks.BasicModuleLoader()
  m = loader.find_module_in_dir(module_name, dirpath)
  if m:
    return loader.load_module(module_name, m)
  else:
    raise IOError("path not found: %s" % dirpath)