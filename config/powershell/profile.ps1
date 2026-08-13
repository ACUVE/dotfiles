# PowerShell プロファイル（dotfiles 管理）
#
# 配置先は OS によって異なる:
#   Windows     : ~/Documents/PowerShell/profile.ps1   （install.sh が個別にリンク）
#   macOS/Linux : ~/.config/powershell/profile.ps1     （CONFIG_FILES の powershell でカバー）
#
# CurrentUserAllHosts に相当するため、pwsh のどのホスト（コンソール / VS Code 等）でも読まれる。

# ------------------------------------------------------------
# mise に GitHub トークンを渡す
#
# mise は `= "latest"` 指定のツールを解決する際に GitHub API を叩く。
# 未認証だとレート制限（60 req/h）に当たり、シェル起動のたびに
# 大量の警告とリトライで数十秒待たされることがある。
#
# ※ mise.toml の [env] に書いても意味がない。mise は自身の設定を解決し終える
#    前に API を叩くため間に合わない（実測で確認済み）。加えて mise の
#    exec() テンプレートはシェルを介さないので `|| true` のような
#    フォールバックも書けない。よって activate より前のここで設定する。
# ------------------------------------------------------------
if (-not $env:MISE_GITHUB_TOKEN -and (Get-Command gh -ErrorAction SilentlyContinue)) {
    $miseGhToken = & gh auth token 2>$null
    if ($LASTEXITCODE -eq 0 -and $miseGhToken) {
        $env:MISE_GITHUB_TOKEN = $miseGhToken.Trim()
    }
    Remove-Variable miseGhToken -ErrorAction SilentlyContinue
}

# ------------------------------------------------------------
# mise
#
# shims が PATH に入っているだけではツールの解決しかできず、
# [env] と [shell_alias] が適用されない。activate して初めて全機能が効く。
# ------------------------------------------------------------
if (Get-Command mise -ErrorAction SilentlyContinue) {
    (& mise activate pwsh) | Out-String | Invoke-Expression
}

# ------------------------------------------------------------
# claude
#
# user スコープの MCP は ~/.claude.json に書かれて symlink 不能なので、
# --mcp-config で dotfiles 管理の別ファイルから読ませる。
#
# ※ mise の [shell_alias] は bash/zsh 向けにしか出力されず pwsh では効かない
#    （mise hook-env -s bash には alias があるが -s pwsh には無い。実測で確認済み）。
#    そのため config/mise/config.toml の shell_alias と同等の内容をここで定義する。
#    片方だけ変更しないこと。
# ------------------------------------------------------------
$global:DotfilesClaudeExe = (
    Get-Command claude -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
).Source
if ($global:DotfilesClaudeExe) {
    function global:claude {
        $configDir = if ($env:CLAUDE_CONFIG_DIR) {
            $env:CLAUDE_CONFIG_DIR
        } else {
            Join-Path $HOME '.config' 'claude'
        }
        & $global:DotfilesClaudeExe --mcp-config (Join-Path $configDir 'mcp.json') @args
    }
}
