'''
The script looks at all the files under the variable dirname, and creates a sorted list based on the files and
creates a PDF
'''

import os
import img2pdf
import argparse


### Specify the input variables
parser=argparse.ArgumentParser()
parser.add_argument("--images_dir", dest="images_dir", type=str,
                        help="Specify the directory where the images reside", required=True, default=None)
parser.add_argument("--pdf_name", dest="pdf_name", type=str,
                        help="Specify the name of the pdf file (with .pdf extension)", required=True, default=None)
parser.add_argument("--pdf_dir", dest="pdf_dir", type=str,
                        help="Specify the name of the directory where the pdf file will be saved", required=True, default=None)
args=parser.parse_args()


images_dir = args.images_dir
pdf_name = args.pdf_name
pdf_dir = args.pdf_dir
imgs = []
sorted_path=[]

def file_sort(images_dir):
    ### extract the file number from the file name and convert to an integer
    for image in (os.listdir(images_dir)):
        # print (fname[:-4], images_dir)
        imgs.append(int(image[:-4]))


def pdf_create(pdf_dir, pdf_name):
    ### Sort the file numbers and create a PDF
    for fname in sorted(imgs):
        path = images_dir +'/' + str(fname)+'.jpg'
        sorted_path.append(path)
    with open(pdf_dir+'/'+pdf_name,"wb") as f:
        f.write(img2pdf.convert(sorted_path))


if __name__ == "__main__":
    file_sort(images_dir)
    pdf_create(pdf_dir, pdf_name)