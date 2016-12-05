in_memory = StringIO()
    zip = ZipFile(in_memory, "a")

    zip.writestr("file1.txt", "some text contents")
    zip.writestr("file2.csv", "csv,data,here")
    
    # fix for Linux zip files read in Windows
    for file in zip.filelist:
        file.create_system = 0

    zip.close()

    response = HttpResponse(mimetype="application/zip")
    response["Content-Disposition"] = "attachment; filename=two_files.zip"

    in_memory.seek(0)
    response.write(in_memory.read())
