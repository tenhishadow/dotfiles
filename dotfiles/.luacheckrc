std = "luajit"

globals = {
  "vim",
}

files[".config/nvim/**/*.lua"] = {
  std = "luajit",
  globals = { "vim" },
}

unused_args = false
allow_defined = true
redefined = false
