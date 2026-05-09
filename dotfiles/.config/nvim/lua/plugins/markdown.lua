local function markdown_preview_platform()
  if vim.fn.has("win32") == 1 or vim.fn.has("win64") == 1 then
    return "win"
  end
  if vim.fn.has("mac") == 1 or vim.fn.has("macvim") == 1 then
    if vim.fn.system("arch"):match("arm64") then
      return "macos-arm64"
    end
    return "macos"
  end
  return "linux"
end

local function markdown_preview_binary(plugin_dir)
  local binary = plugin_dir .. "/app/bin/markdown-preview-" .. markdown_preview_platform()
  if vim.fn.has("win32") == 1 or vim.fn.has("win64") == 1 then
    binary = binary .. ".exe"
  end
  return binary
end

local function markdown_preview_binary_version(binary)
  if vim.fn.executable(binary) ~= 1 then
    return nil
  end

  local output = vim.fn.system({ binary, "--version" })
  if vim.v.shell_error ~= 0 then
    return nil
  end

  return output:match("^%s*(.-)%s*$")
end

local function markdown_preview_version(plugin_dir)
  local package_json = plugin_dir .. "/package.json"
  local ok, lines = pcall(vim.fn.readfile, package_json)
  if not ok then
    error("Failed to read markdown-preview package metadata: " .. package_json)
  end

  local ok_json, package = pcall(vim.fn.json_decode, table.concat(lines, "\n"))
  if not ok_json or type(package) ~= "table" or type(package.version) ~= "string" then
    error("Failed to parse markdown-preview package metadata: " .. package_json)
  end

  return package.version
end

local function run_markdown_preview_install(plugin)
  local plugin_dir = plugin.dir
  local package_version = markdown_preview_version(plugin_dir)
  local binary = markdown_preview_binary(plugin_dir)

  if markdown_preview_binary_version(binary) == package_version then
    return
  end

  local install_script = plugin_dir .. "/app/install.sh"
  local install_cmd = plugin_dir .. "/app/install.cmd"
  local version = "v" .. package_version
  local command

  if vim.fn.has("win32") == 1 or vim.fn.has("win64") == 1 then
    command = { install_cmd, version }
  else
    command = { "sh", install_script, version }
  end

  local output = vim.fn.system(command)
  if vim.v.shell_error ~= 0 then
    error("markdown-preview install failed:\n" .. output)
  end

  if markdown_preview_binary_version(binary) ~= package_version then
    error("markdown-preview install did not create expected executable: " .. binary)
  end
end

return {
  -- Markdown syntax / motions
  { "preservim/vim-markdown", ft = { "markdown", "vimwiki" } },

  -- Live Markdown preview in browser
  {
    "iamcco/markdown-preview.nvim",
    ft = { "markdown", "vimwiki" },
    cmd = { "MarkdownPreview", "MarkdownPreviewToggle", "MarkdownPreviewStop" },
    build = run_markdown_preview_install,
    init = function()
      vim.g.mkdp_filetypes = { "markdown", "vimwiki" }

      vim.g.mkdp_auto_start = 0
      vim.g.mkdp_auto_close = 1
    end,
  },
}
