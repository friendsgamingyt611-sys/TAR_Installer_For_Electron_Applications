# Fish completion for tifea

complete -c tifea -n "__fish_use_subcommand" -a "install" -d "Install a prebuilt Electron tarball"
complete -c tifea -n "__fish_use_subcommand" -a "reinstall" -d "Reinstall an existing application"
complete -c tifea -n "__fish_use_subcommand" -a "check" -d "Check installation integrity"
complete -c tifea -n "__fish_use_subcommand" -a "fix" -d "Repair installed application"
complete -c tifea -n "__fish_use_subcommand" -a "list" -d "List managed applications"
complete -c tifea -n "__fish_use_subcommand" -a "uninstall" -d "Uninstall an application"

complete -c tifea -l dry-run -d "Show plan without making changes"
complete -c tifea -l yes -d "Skip confirmation prompts"
complete -c tifea -l sandbox -r -f -a "apparmor setuid no-sandbox" -d "Sandbox confinement strategy"
complete -c tifea -s h -l help -d "Show help message"
