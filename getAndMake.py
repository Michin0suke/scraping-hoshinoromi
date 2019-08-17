import urllib.request, urllib.error
import img2pdf
from pathlib import Path
import urllib.request, urllib.error
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
import chromedriver_binary
import re, time, datetime, os, sys

# タイトルと対象URLの設定
title = input('title: ')
url = input('url: ')

# ./{title}/IMG/ の再帰的なディレクトリの作成
imgDir = './%s/IMG' % (title)
os.makedirs(imgDir, exist_ok=True)

# URLの区切りをわかりやすくするため(再実行した場合にログの行が重複するため)
# with open('./%s/%s.csv' % (title, title), mode='a', encoding="utf-8") as f:
#   f.write('\n\n')

# 画像のURLの取得
options = Options()
options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
options.add_argument('--headless')
options.add_argument('window-size=600,800')

# executable_pathにはchromedriverのパスを指定。
# Chrome Canaryのバージョンに対応するchromedriverをここからダウンロード→https://chromedriver.chromium.org/downloads
driver = webdriver.Chrome(options=options, executable_path='/Users/michinosuke/webdriver/chromedriver')
driver.get(url)
progressBar = driver.find_element_by_id('progressbar').text
countOfPages = int( re.search(r'(?<=/)\d*', progressBar).group(0) )
print('countOfPages is %s' % (countOfPages))

# 5秒でタイムアウトする。
wait = WebDriverWait(driver, 5)

# 初回アクセスしたときに表示されるintrojs-button要素のポップアップを閉じる。
wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'introjs-button')))
driver.find_element_by_class_name('introjs-button').click()

# _blankでタブが作成されるので、一番右のタブを表示する。
time.sleep(1)
handle_array = driver.window_handles
driver.switch_to.window(handle_array[-1])

for page in range(countOfPages):
  try: 
    i = 0
    while True:
      time.sleep(1)
      # 今のページ数のsrcが読み込まれるまで最大20秒間待つ。
      if driver.find_element_by_id(page+1).get_attribute('src') == '':
        i += 1
        print('  waiting for page %d : %ds' % (page+1, i))
        if i >= 20:
          # 20秒経っても復帰しない場合はプログラムを再実行(動作確認なし)
          print('[ this program will be reloaded. ]')
          os.execv(sys.executable, os.path.abspath(__file__))
        try:
          # アラートが表示されている場合は消す
          Alert(driver).accept()
          print('    The alert has been canceled.')
        except:
          pass
      else:
        print('got url %d/%d' % (page+1, countOfPages))
        break

    # 取得した画像のURLをCSVファイルに書き込む
    imgurl = driver.find_element_by_id(page+1).get_attribute('src')
    with open('./%s/%s.csv' % (title, title), mode='a', encoding="utf-8") as f:
      f.write('%d,%s\n' % (page+1, imgurl))

    # 要素nextをクリックして次のページに繊維する。
    actions = ActionChains(driver)
    elements = WebDriverWait(driver, 8).until(
      EC.presence_of_element_located((By.ID , "next"))
    )
    actions.move_to_element(elements)
    actions.click()
    actions.perform()
  except Exception as err:
    print(err)
    
driver.close()
driver.quit()


# 画像のダウンロード
page = 1
with open('./%s/%s.csv' % (title, title), mode='r', encoding="utf-8") as f:
  while True:
    line = f.readline()
    if not line:
      print('Images have been downloaded.')
      break
    elif line == '\n':
      print('  continue')
      continue
    url = line.split(',')[1]
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    strpage = str(page).zfill(3)
    urllib.request.urlretrieve(url, './%s/IMG/%s-%s.jpg' % (title, title, strpage))
    print(url, './%s/IMG/%s-%s.jpg' % (title, title, strpage))
    page += 1


# PDFの作成
outputpath = Path('./%s/%s.pdf' % (title, title))
inputpath = Path('./%s/IMG/' % (title))

lists = list(inputpath.glob("**/*"))
with open(outputpath,"wb") as f:
  f.write(img2pdf.convert([str(i) for i in sorted(lists) if i.match("*.jpg") or i.match("*.png")]))

print(outputpath.name + " :Done")
