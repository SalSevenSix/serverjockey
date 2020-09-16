from core import util


def _function_find_steamcmd():
    return util.to_text((
        'find_steamcmd() {',
        '  steamcmd +quit >/dev/null 2>&1 && echo steamcmd && return 0',
        '  steamcmd.sh +quit >/dev/null 2>&1 && echo steamcmd.sh && return 0',
        '  ~/Steam/steamcmd.sh +quit >/dev/null 2>&1 && echo ~/Steam/steamcmd.sh && return 0',
        '  echo steamcmd && return 1',
        '}'))


def steamcmd_app_update(**kwargs):
    line = ['+login anonymous',
            '+force_install_dir {install_dir}',
            '+app_update {app_id}']
    if util.get('beta', kwargs):
        line.append('-beta {beta}')
    if util.get('validate', kwargs):
        line.append('validate')
    line.append('+quit')
    line = ' '.join(line).format(**kwargs)
    return util.to_text((_function_find_steamcmd(), '$(find_steamcmd) ' + line))
