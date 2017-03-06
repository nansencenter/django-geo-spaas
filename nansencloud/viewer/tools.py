import os
from django.conf import settings

def module_media_path(module):
    media_path = settings.MEDIA_ROOT
    for m in module.split('.'):
        media_path = os.path.join(media_path, m)
        if not os.path.exists(media_path):
            os.mkdir(media_path)
    return media_path


def media_path(module, filename):

    # Check that the file exists
    if not os.path.exists(filename):
        raise IOError('%s: File does not exist' %filename)

    media_path = module_media_path(module)

    # Get the path of media files created from <filename>
    basename = os.path.split(filename)[-1].split('.')[0]
    dataset_media_path = os.path.join(media_path, basename)
    if not os.path.exists(dataset_media_path):
        os.mkdir(dataset_media_path)

    return dataset_media_path
