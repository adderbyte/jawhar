جوهرة الصحراء — دليل المحتوى / Content guide

1) Each item = one folder inside content/ (image + info.txt [+ text/PDF]). Same file names everywhere:
   maqalat/<date>-<name>/                   image.jpg  info.txt  text.txt  (maqala.pdf)
   isdarat/kutub/<name>/                    cover.jpg  info.txt  kitab.pdf
   isdarat/majallat/<name>/                 cover.jpg  info.txt  adad.pdf
   baramij/<NN-name>/                       image.jpg  info.txt
   ashkhas/kuttab-wa-bahithun/<NN-name>/    photo.jpg  info.txt
   ashkhas/fariq-al-amal/<NN-name>/         photo.jpg  info.txt
   site/                          logo.jpg  banner.jpg  info.txt (contact)
2) To add an item: copy a folder from content/_namadhij/ (or any existing item), rename it
   (latinized Arabic, lowercase, hyphens), fill info.txt, replace the image.
3) To replace an image: overwrite the file, keeping the same name.
4) To remove an item: delete its folder.
5) After any change run:  python build.py   -> regenerates index.html
6) Upload index.html + content/ to your host (keep them together).
Tip: click "دليل الاستبدال" on the page to see which file each image slot expects.
