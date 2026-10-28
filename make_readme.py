import re

path = r'C:\Users\guntu\OneDrive\Desktop\readme-github\RupakGunturu\README_new.md'
with open(path, encoding='utf-8') as f:
    s = f.read()

s = s.replace('avi-ascii.svg', 'rupak-ascii.svg')
s = s.replace('avi@github', 'rupak@github')
s = s.replace('Avi Vashishta', 'Rupak Gunturu')
s = s.replace("Avi's GitHub", "Rupak's GitHub")
s = s.replace('Avi Vashishta \u2014 ASCII portrait', 'Rupak Gunturu \u2014 ASCII portrait')
s = s.replace('Fullstack Developer \u00b7 AI Builder \u00b7 Instructor', 'Software Developer')

s = s.replace('[![Portfolio](https://img.shields.io/badge/Portfolio-avivashishta.com-0d1117?style=for-the-badge&logo=vercel&logoColor=white)](https://www.avivashishta.com)\n', '')
s = s.replace('[![Instagram](https://img.shields.io/badge/Instagram-avi__vashishta29-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/avi_vashishta29)\n', '')
s = s.replace('[![Live Terminal](https://img.shields.io/badge/\u26a1_Live_Terminal-avivashishta29.github.io-22d3ee?style=for-the-badge&logo=gnometerminal&logoColor=black)](https://avivashishta29.github.io)\n', '')
s = s.replace('[![LinkedIn](https://img.shields.io/badge/LinkedIn-avivashishta-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/avivashishta)',
              '[![LinkedIn](https://img.shields.io/badge/LinkedIn-rupak--gunturu-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/rupak-gunturu-52568a2b9)')
if '[![email]' not in s:
    s = s.replace('](https://linkedin.com/in/rupak-gunturu-52568a2b9)\n',
                  '](https://linkedin.com/in/rupak-gunturu-52568a2b9) [![email](https://img.shields.io/badge/Email-D14836?logo=gmail&logoColor=white)](mailto:ravi.genzgalaxy@gmail.com)\n')

out = r'C:\Users\guntu\OneDrive\Desktop\readme-github\RupakGunturu\README_terminal.md'
with open(out, 'w', encoding='utf-8') as f:
    f.write(s)
print('done')
