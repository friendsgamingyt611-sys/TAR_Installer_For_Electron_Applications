# tifea completion for Bash

_tifea_completions() {
    local cur prev words cword
    _init_completion || return

    local commands="install reinstall check fix list uninstall"
    local options="--dry-run --yes --sandbox -h --help"
    local sandbox_opts="apparmor setuid no-sandbox"

    if [[ ${cword} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands} ${options}" -- "${cur}") )
        return 0
    fi

    case "${prev}" in
        --sandbox)
            COMPREPLY=( $(compgen -W "${sandbox_opts}" -- "${cur}") )
            return 0
            ;;
        install|reinstall|check|fix)
            _filedir
            return 0
            ;;
        uninstall)
            local installed_apps=""
            if [[ -d "$HOME/.local/share/tifea" ]]; then
                installed_apps=$(command ls -1 "$HOME/.local/share/tifea" 2>/dev/null)
            elif [[ -d "$HOME/.local/share/targz-installer" ]]; then
                installed_apps=$(command ls -1 "$HOME/.local/share/targz-installer" 2>/dev/null)
            fi
            COMPREPLY=( $(compgen -W "${installed_apps}" -- "${cur}") )
            return 0
            ;;
    esac

    COMPREPLY=( $(compgen -W "${options}" -- "${cur}") )
}

complete -F _tifea_completions tifea tifiea targz-installer
