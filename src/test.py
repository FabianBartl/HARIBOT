import gzip, os
from ynlib.files import ReadFromFile, WriteToFile
from ynlib.system import Execute
from xml.dom.minidom import parseString


def SVGToJPGInMemory(svgPath, newWidth, backgroundColor):

    tempPath = r"C:\Users\fabia\OneDrive\Dokumente\GitHub\HARIBOT\tmp"
    fileNameRoot = 'score_test'

    if svgPath.lower().endswith('svgz'):
        svg = gzip.open(svgPath, 'rb').read()
    else:
        svg = ReadFromFile(svgPath)

    xmldoc = parseString(svg)

    width = float(xmldoc.getElementsByTagName("svg")[0].attributes['width'].value.split('px')[0])
    height = float(xmldoc.getElementsByTagName("svg")[0].attributes['height'].value.split('px')[0])

    newHeight = int(newWidth / width * height) 

    xmldoc.getElementsByTagName("svg")[0].attributes['width'].value = '%spx' % newWidth
    xmldoc.getElementsByTagName("svg")[0].attributes['height'].value = '%spx' % newHeight

    WriteToFile(os.path.join(tempPath, fileNameRoot + '.svg'), xmldoc.toxml())
    Execute('convert -background "%s" %s %s' % (backgroundColor, os.path.join(tempPath, fileNameRoot + '.svg'), os.path.join(tempPath, fileNameRoot + '.jpg')))

    jpg = open(os.path.join(tempPath, fileNameRoot + '.jpg'), 'rb').read()

    os.remove(os.path.join(tempPath, fileNameRoot + '.jpg'))
    os.remove(os.path.join(tempPath, fileNameRoot + '.svg'))

SVGToJPGInMemory(r"C:\Users\fabia\OneDrive\Dokumente\GitHub\HARIBOT\tmp\score.svg", 400, "rgb(50, 53, 59)")
