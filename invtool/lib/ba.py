#!/usr/bin/env python
import simplejson as json
import shlex
import io

from invtool.main import do_dispatch


class BAError(Exception):
    def __init__(self, error=None):
        self.error = error
        return super(BAError, self).__init__()


def ba_export_systems_raw(search):
    command = 'ba_export --query {0}'.format(search)
    nas, (resp_code, resp_list) = do_dispatch(shlex.split(command))
    raw_json = '\n'.join(resp_list)
    if 'errors' in raw_json:
        return None, raw_json
    return json.loads(raw_json), None


def ba_export_systems_regex(search):
    """
    Export systems based on a regex search pattern. You can use
    https://inventory.mozilla.org/en-US/core/search/ to test out your regex.

    """
    return ba_export_systems_raw("/{search}".format(search=search))


def ba_export_systems_hostname_list(hostnames):
    """
    Export a list of systems by hostname.

    :param hostnames: A list of full hostnames that will be looked up in a
        single api call.
    :type hostnames: list

    """
    search = '"{search}"'.format(
        search=' OR '.join(map(lambda h: "/^{h}$".format(h=h), hostnames))
    )
    return ba_export_systems_raw(search)


def ba_import(dict_blob):
    """
    Import a blob of data. The data you pass in should have been originally
    exported via one of the ``ba_export`` functions.

    This function will convert the passed python dictionary into a JSON
    dictionary before sending it to Inventory to be processed.

    This function will return a dictionary and if that dictionary has the key
    'errors' then there were errors and nothing was saved during processing.

    :param dict_blob: A blob of data to import
    :type dict_blob: dict

    """
    json_blob = json.dumps(dict_blob)
    with io.BytesIO(json_blob) as json_blob_fd:
        nas, (resp_code, resp_list) = do_dispatch(
            ['ba_import'], IN=json_blob_fd
        )
        raw_json = '\n'.join(resp_list)
        if 'errors' in raw_json:
            return None, raw_json
        return json.loads(raw_json), None


def removes_pk_attrs(blobs):
    """
    This function has sideaffects.
    """
    try:
        for blob in blobs:
            remove_pk_attrs(blob)
    except TypeError:
        remove_pk_attrs(blobs)
    return


def remove_pk_attrs(blob):
    if not isinstance(blob, dict):
        return
    blob.pop('pk', None)
    for attr, value in blob.iteritems():
        if isinstance(value, list):
            removes_pk_attrs(value)


def export_system_template(hostname):
    template, error = ba_export_systems_hostname_list([hostname])
    if error:
        raise BAError(error=error)
    if len(template['systems']) != 1:
        raise BAError(error={
            'errors': 'The hostname for the system template you provided did '
            'not correspond to a single system'
        })
    system_template = template['systems']
    removes_pk_attrs(system_template)
    return system_template