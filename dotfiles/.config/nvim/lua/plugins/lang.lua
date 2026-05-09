return {
  -- Python virtualenv helper
  { "plytophogy/vim-virtualenv", ft = { "python" } },

  -- HashiCorp / cloud / infra tooling
  { "zainin/vim-mikrotik", ft = { "rsc" } },
  { "hashivim/vim-terraform", ft = { "hcl", "terraform" } },
  { "hashivim/vim-consul", cmd = { "Consul" } },
  { "hashivim/vim-nomadproject", cmd = { "Nomad" } },
  { "hashivim/vim-vagrant", cmd = { "Vagrant" } },
  { "hashivim/vim-vaultproject", cmd = { "Vault" } },
  { "speshak/vim-cfn", ft = { "cloudformation", "json.cloudformation", "yaml.cloudformation" } },

  -- Misc languages
  { "vim-ruby/vim-ruby", ft = { "eruby", "ruby" } },
  { "chr4/nginx.vim", ft = { "nginx" } },
}
