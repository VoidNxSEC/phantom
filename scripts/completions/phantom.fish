_python_mphantomclimain_completion() {
    local IFS=$'
'
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
                   COMP_CWORD=$COMP_CWORD \
                   _PYTHON _M PHANTOM.CLI.MAIN_COMPLETE=complete_bash $1 ) )
    return 0
}

complete -o default -F _python_mphantomclimain_completion python -m phantom.cli.main
