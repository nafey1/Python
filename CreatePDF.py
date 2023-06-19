'''
The script looks at all the files under the variable dirname, and creates a sorted list based on the files and
creates a PDF
'''

import os
import img2pdf
import argparse


### Specify the input variables
parser=argparse.ArgumentParser()
parser.add_argument("--dir_name", dest="dir_name", type=str,
                        help="Specify the directory where the images reside", required=True, default=None)
parser.add_argument("--pdf_name", dest="pdf_name", type=str,
                        help="Specify the name of the pdf file (with .pdf extension)", required=True, default=None)
args=parser.parse_args()


dirname = args.dir_name
imgs = []
sorted_path=[]

### extract the file number from the file name and convert to an integer
for image in (os.listdir(dirname)):
    # print (fname[:-4], dirname)
    imgs.append(int(image[:-4]))


### Sort the file numbers and create a PDF
for fname in sorted(imgs):
    path = dirname +'/' + str(fname)+'.jpg'
    sorted_path.append(path)
with open(args.dir_name+'/'+args.pdf_name,"wb") as f:
    f.write(img2pdf.convert(sorted_path))








