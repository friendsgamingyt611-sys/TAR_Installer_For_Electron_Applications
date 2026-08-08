#compdef tifea tifiea targz-installer

_tifea() {
    local -a commands
    commands=(
        'install:Install a prebuilt Electron tarball safely'
        'reinstall:Replace an existing application installation with a new tarball'
        'check:Verify installation integrity against a tarball'
        'fix:Repair missing symlinks, desktop entries, or sandbox profiles'
        'list:List all applications currently managed by TIFEA'
        'uninstall:Safely remove an installed application and restore backups'
    )

    _arguments -C \
        '(-h --help)'{-h,--help}'[Show help message and exit]' \
        '--dry-run[Display execution plan without making changes]' \
        '--yes[Skip confirmation prompts]' \
        '--sandbox[Specify sandbox strategy]:sandbox:(apparmor setuid no-sandbox)' \
        '1: :->command' \
        '*:: :->args'

    case $state in
        command)
            _describe -t commands 'tifea command' commands
            ;;
        args)
            case $line[1] in
                install|reinstall|check|fix)
                    _files
                    ;;
                uninstall)
                    local -a apps
                    if [[ -d "$HOME/.local/share/tifea" ]]; then
                        apps=(${$(ls "$HOME/.local/share/tifea"):#*})
                    fi
                    _describe -t apps 'installed application' apps
                    ;;
            esac
            ;;
    esac
}

_tifea "$@"
