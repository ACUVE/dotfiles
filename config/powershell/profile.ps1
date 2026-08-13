# PowerShell プロファイル（dotfiles 管理）
#
# 配置先は OS によって異なる:
#   Windows     : ~/Documents/PowerShell/profile.ps1   （install.sh が個別にリンク）
#   macOS/Linux : ~/.config/powershell/profile.ps1     （CONFIG_FILES の powershell でカバー）
#
# CurrentUserAllHosts に相当するため、pwsh のどのホスト（コンソール / VS Code 等）でも読まれる。

# mise
#
# shims が PATH に入っているだけではツールの解決しかできず、
# [env] が適用されない。activate して初めて効く。
if (Get-Command mise -ErrorAction SilentlyContinue) {
    (& mise activate pwsh) | Out-String | Invoke-Expression
}
