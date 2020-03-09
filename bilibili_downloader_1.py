import json
import os
import re
import shutil
import ssl
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from lxml import etree

# 设置请求头等参数，防止被反爬
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36'
}
params = {
    'from': 'search',
    'seid': '9698329271136034665'
}


def re_video_info(text, pattern):
    '''利用正则表达式匹配出视频信息并转化成json'''
    match = re.search(pattern, text)
    return json.loads(match.group(1))


def create_folder(aid):
    '''创建文件夹'''
    if not os.path.exists(aid):
        os.mkdir(aid)


def remove_move_file(aid):
    '''删除和移动文件'''
    file_list = os.listdir('./')
    for file in file_list:
        # 移除临时文件
        if file.endswith('_video.mp4'):
            os.remove(file)
            pass
        elif file.endswith('_audio.mp4'):
            os.remove(file)
            pass
        # 保存最终的视频文件
        elif file.endswith('.mp4'):
            if os.path.exists(aid + '/' + file):
                os.remove(aid + '/' + file)
            shutil.move(file, aid)


def download_video_batch(referer_url, video_url, audio_url, video_name, index):
    '''批量下载系列视频'''
    # 更新请求头
    headers.update({"Referer": referer_url})
    # headers.update({"User-Agent": get_user_agent()})
    # 获取文件名
    short_name = video_name.split('/')[2]
    print("%d.\t视频下载开始：%s" % (index, short_name))
    # 下载并保存视频
    video_content = requests.get(video_url, headers=headers)
    print('%d.\t%s\t视频大小：' % (index, short_name),
          round(int(video_content.headers.get('content-length', 0)) / 1024 / 1024, 2), '\tMB')
    received_video = 0
    with open('%s_video.mp4' % video_name, 'ab') as output:
        headers['Range'] = 'bytes=' + str(received_video) + '-'
        response = requests.get(video_url, headers=headers)
        output.write(response.content)
    # 下载并保存音频
    audio_content = requests.get(audio_url, headers=headers)
    print('%d.\t%s\t音频大小：' % (index, short_name),
          round(int(audio_content.headers.get('content-length', 0)) / 1024 / 1024, 2), '\tMB')
    received_audio = 0
    with open('%s_audio.mp4' % video_name, 'ab') as output:
        headers['Range'] = 'bytes=' + str(received_audio) + '-'
        response = requests.get(audio_url, headers=headers)
        output.write(response.content)
        received_audio += len(response.content)
    return video_name, index


def download_video_single(referer_url, video_url, audio_url, video_name):
    '''单个视频下载'''
    # 更新请求头
    headers.update({"Referer": referer_url})
    # headers.update({"User-Agent": get_user_agent()})
    print("视频下载开始：%s" % video_name)
    # 下载并保存视频
    video_content = requests.get(video_url, headers=headers)
    print('%s\t视频大小：' % video_name, round(int(video_content.headers.get('content-length', 0)) / 1024 / 1024, 2), '\tMB')
    received_video = 0
    with open('%s_video.mp4' % video_name, 'ab') as output:
        headers['Range'] = 'bytes=' + str(received_video) + '-'
        response = requests.get(video_url, headers=headers)
        output.write(response.content)
    # 下载并保存音频
    audio_content = requests.get(audio_url, headers=headers)
    print('%s\t音频大小：' % video_name, round(int(audio_content.headers.get('content-length', 0)) / 1024 / 1024, 2), '\tMB')
    received_audio = 0
    with open('%s_audio.mp4' % video_name, 'ab') as output:
        headers['Range'] = 'bytes=' + str(received_audio) + '-'
        response = requests.get(audio_url, headers=headers)
        output.write(response.content)
        received_audio += len(response.content)
    print("视频下载结束：%s" % video_name)
    video_audio_merge_single(video_name)


def video_audio_merge_batch(result):
    '''使用ffmpeg批量视频音频合并'''
    video_name = result.result()[0]
    index = result.result()[1]
    import subprocess
    video_final = video_name.replace('video', 'video_final')
    command = 'ffmpeg -i %s_video.mp4 -i %s_audio.mp4 -c copy %s.mp4 -y -loglevel quiet' % (
        video_name, video_name, video_final)
    subprocess.Popen(command, shell=True)
    print("%d.\t视频下载结束：%s" % (index, video_name.split('/')[2]))


def video_audio_merge_single(video_name):
    '''使用ffmpeg单个视频音频合并'''
    print("视频合成开始：%s" % video_name)
    import subprocess
    command = 'ffmpeg -i %s_video.mp4 -i %s_audio.mp4 -c copy %s.mp4 -y -loglevel quiet' % (
        video_name, video_name, video_name)
    subprocess.Popen(command, shell=True)
    print("视频合成结束：%s" % video_name)


def batch_download():
    '''使用多线程批量下载视频'''
    # 提示输入需要下载的系列视频对应的id
    aid = input('请输入要下载的视频id（举例：链接https://www.bilibili.com/video/av91748877?p=1中id为91748877），默认为91748877\t')
    if aid:
        pass
    else:
        aid = '91748877'
    # 提示选择清晰度
    quality = input('请选择清晰度（1代表高清，2代表清晰，3代表流畅），默认高清\t')
    if quality == '2':
        pass
    elif quality == '3':
        pass
    else:
        quality = '1'
    acc_quality = int(quality) - 1
    # ssl模块，处理https请求失败问题，生成证书上下文
    ssl._create_default_https_context = ssl._create_unverified_context
    # 获取视频主题
    url = 'https://www.bilibili.com/video/av{}?p=1'.format(aid)
    html = etree.HTML(requests.get(url, params=params, headers=headers).text)
    title = html.xpath('//*[@id="viewbox_report"]/h1/span/text()')[0]
    print('您即将下载的视频系列是：', title)
    # 创建临时文件夹
    create_folder('video')
    create_folder('video_final')
    # 定义一个线程池，大小为3
    pool = ThreadPoolExecutor(3)
    # 通过api获取视频信息
    res_json = requests.get('https://api.bilibili.com/x/player/pagelist?aid={}'.format(aid)).json()
    video_name_list = res_json['data']
    print('共下载视频{}个'.format(len(video_name_list)))
    for i, video_content in enumerate(video_name_list):
        video_name = ('./video/' + video_content['part']).replace(" ", "-")
        origin_video_url = 'https://www.bilibili.com/video/av{}'.format(aid) + '?p=%d' % (i + 1)
        # 请求视频，获取信息
        res = requests.get(origin_video_url, headers=headers)
        # 解析出视频详情的json
        video_info_temp = re_video_info(res.text, '__playinfo__=(.*?)</script><script>')
        video_info = {}
        # 获取视频品质
        quality = video_info_temp['data']['accept_description'][acc_quality]
        # 获取视频时长
        video_info['duration'] = video_info_temp['data']['dash']['duration']
        # 获取视频链接
        video_url = video_info_temp['data']['dash']['video'][acc_quality]['baseUrl']
        # 获取音频链接
        audio_url = video_info_temp['data']['dash']['audio'][acc_quality]['baseUrl']
        # 计算视频时长
        video_time = int(video_info.get('duration', 0))
        video_minute = video_time // 60
        video_second = video_time % 60
        print('{}.\t当前视频清晰度为{}，时长{}分{}秒'.format(i + 1, quality, video_minute, video_second))
        # 将任务加入线程池，并在任务完成后回调完成视频音频合并
        pool.submit(download_video_batch, origin_video_url, video_url, audio_url, video_name, i + 1).add_done_callback(
            video_audio_merge_batch)
    pool.shutdown(wait=True)
    time.sleep(5)
    # 整理视频信息
    if os.path.exists(title):
        shutil.rmtree(title)
    os.rename('video_final', title)
    try:
        shutil.rmtree('video')
    except:
        shutil.rmtree('video')


def multiple_download():
    '''批量下载多个独立视频'''
    # 提示输入所有aid
    aid_str = input(
        '请输入要下载的所有视频id，id之间用空格分开\n举例：有5个链接https://www.bilibili.com/video/av89592082、https://www.bilibili.com/video/av68716174、https://www.bilibili.com/video/av87216317、\nhttps://www.bilibili.com/video/av83200644和https://www.bilibili.com/video/av88252843，则输入89592082 68716174 87216317 83200644 88252843\n默认为89592082 68716174 87216317 83200644 88252843\t')
    if aid_str:
        pass
    else:
        aid_str = '89592082 68716174 87216317 83200644 88252843'
    if os.path.exists(aid_str):
        shutil.rmtree(aid_str)
    aids = aid_str.split(' ')
    # 提示选择视频质量
    quality = input('请选择清晰度（1代表高清，2代表清晰，3代表流畅），默认高清\t')
    if quality == '2':
        pass
    elif quality == '3':
        pass
    else:
        quality = '1'
    acc_quality = int(quality) - 1
    # 创建文件夹
    create_folder(aid_str)
    # 创建线程池，执行多任务
    pool = ThreadPoolExecutor(3)
    for aid in aids:
        # 将任务加入线程池
        pool.submit(single_download, aid, acc_quality)
    pool.shutdown(wait=True)
    time.sleep(5)
    # 删除临时文件，移动文件
    remove_move_file(aid_str)


def single_download(aid, acc_quality):
    '''单个视频实现下载'''
    # 请求视频链接，获取信息
    origin_video_url = 'https://www.bilibili.com/video/av' + aid
    res = requests.get(origin_video_url, headers=headers)
    html = etree.HTML(res.text)
    title = html.xpath('//*[@id="viewbox_report"]/h1/span/text()')[0]
    print('您当前正在下载：', title)
    video_info_temp = re_video_info(res.text, '__playinfo__=(.*?)</script><script>')
    video_info = {}
    # 获取视频质量
    quality = video_info_temp['data']['accept_description'][acc_quality]
    # 获取视频时长
    video_info['duration'] = video_info_temp['data']['dash']['duration']
    # 获取视频链接
    video_url = video_info_temp['data']['dash']['video'][acc_quality]['baseUrl']
    # 获取音频链接
    audio_url = video_info_temp['data']['dash']['audio'][acc_quality]['baseUrl']
    # 计算视频时长
    video_time = int(video_info.get('duration', 0))
    video_minute = video_time // 60
    video_second = video_time % 60
    print('当前视频清晰度为{}，时长{}分{}秒'.format(quality, video_minute, video_second))
    # 调用函数下载保存视频
    download_video_single(origin_video_url, video_url, audio_url, title)


def single_input():
    '''单个文件下载，获取参数'''
    # 获取视频aid
    aid = input('请输入要下载的视频id（举例：链接https://www.bilibili.com/video/av89592082中id为89592082），默认为89592082\t')
    if aid:
        pass
    else:
        aid = '89592082'
        # 提示选择视频质量
    quality = input('请选择清晰度（1代表高清，2代表清晰，3代表流畅），默认高清\t')
    if quality == '2':
        pass
    elif quality == '3':
        pass
    else:
        quality = '1'
    acc_quality = int(quality) - 1
    # 调用函数进行下载
    single_download(aid, acc_quality)


def main():
    '''主函数，提示用户进行三种下载模式的选择'''
    download_choice = input('请输入您需要下载的类型：\n1代表下载单个视频，2代表批量下载系列视频，3代表批量下载多个不同视频，默认下载单个视频\t')
    # 批量下载系列视频
    if download_choice == '2':
        batch_download()
    # 批量下载多个单个视频
    elif download_choice == '3':
        multiple_download()
    # 下载单个视频
    else:
        single_input()


if __name__ == '__main__':
    '''调用主函数'''
    main()