from PIL import Image, ExifTags

def scrub_sensitive_exif(exif: Image.Exif) -> Image.Exif:
    ifd_exif = exif.get_ifd(ExifTags.IFD.Exif)
    # Remove tags related to size and format if they exist
    tags_to_keep = set([
        ExifTags.Base.DateTime,
        ExifTags.Base.OffsetTime,
        ExifTags.Base.DateTimeOriginal,
        ExifTags.Base.OffsetTimeOriginal,
        ExifTags.Base.DateTimeDigitized,
        ExifTags.Base.OffsetTimeDigitized,
        ExifTags.Base.TimeZoneOffset,
        ExifTags.IFD.GPSInfo,
        ExifTags.Base.Orientation, # TODO: remove if ever using Transpose().
    ])
    for tag_to_remove in set(exif) - tags_to_keep:
        del exif[tag_to_remove]
    
    for tag_in_ifd_exif_to_remove in set(ifd_exif) - tags_to_keep:
        del ifd_exif[tag_in_ifd_exif_to_remove]

    exif._ifds[ExifTags.IFD.Exif] = ifd_exif

    return exif