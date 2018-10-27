import requests
from fake_useragent import UserAgent
from lxml import etree
from queue import Queue
from threading import Thread
from time import sleep
headers = {
    'User-Agent':UserAgent().random
}

#基础url
p_url = 'https://wenda.autohome.com.cn'
#一级url
c_url ='https://wenda.autohome.com.cn/topic/list-%s-0-0-0-0-1'
#二级url
s_url = 'https://wenda.autohome.com.cn/topic/list-1-%s-0-0-0-2'
#三级url
ss_url = 'https://wenda.autohome.com.cn/topic/list-2-31-%s-0-0-1'
#拿到一二三级url函数
def get_all_html(i,q):
    c_url = 'https://wenda.autohome.com.cn/topic/list-%s-0-0-0-0-1'%i
    resp = requests.get(c_url,headers=headers)
    e = etree.HTML(resp.text)

    #当前一级url下面的所有子路由
    s_url_list = e.xpath('//div[@class="question-filter"]/div[3]//a/@href')

    if s_url_list:
        for s_url in range(len(s_url_list)):
            q.put(s_url_list[s_url])
    else:
        q.put(c_url)
    print('头部第%s分析完成'%i)
    # while not q.empty():
    #     print(q.get())

#访问二级标签拿到具体问题的url和拿到三级标签url
def all_html(q2,q):
    # print(q.get())
    while not q.empty() or not q2.empty():
        try:
            print('开始分析二三级url')
            u =q.get()
            url = 'https://wenda.autohome.com.cn'+u
            resp = requests.get(url,headers=headers)
            e = etree.HTML(resp.text)
            # 拿到一、二、三级的名字
            l_name = ''.join(e.xpath('//em[@class="current"]/text()'))
            # 判断是否存在三级url
            ss_url_list = e.xpath('//div[@class="question-filter"]/div[4]//a/@href')

            if ss_url_list:
                if not u in ss_url_list:
                    for ss_url in range(len(ss_url_list)):
                        q.put(ss_url_list[ss_url])
                else:
                    # 每一页问题具体的url
                    q_url_list = e.xpath('//div[@class="question-list-wrapper"]/ul//h4/a/@href')
                    if q_url_list:
                        for i in range(len(q_url_list)):
                            q2.put(q_url_list[i])
                    # 获取下一页标签url
                    next_page_list = e.xpath('//a[@class="athm-page__next"]/@href')
                    if next_page_list:
                        next_url = next_page_list[0]
                        while True:
                            resp2 = requests.get('https://wenda.autohome.com.cn' + next_url, headers=headers)
                            e2 = etree.HTML(resp2.text)
                            # 每一页问题具体的url
                            q2_url_list = e2.xpath('//div[@class="question-list-wrapper"]/ul//h4/a/@href')
                            if q2_url_list:
                                for a in range(len(q2_url_list)):
                                    q2.put(q2_url_list[a])
                            next2_page_list = e2.xpath('//a[@class="athm-page__next"]/@href')
                            print('分析三级页面')
                            if next2_page_list:
                                next_url = next2_page_list[0]
                            else:
                                break
            else:
                #每一页问题具体的url
                q_url_list= e.xpath('//div[@class="question-list-wrapper"]/ul//h4/a/@href')
                if q_url_list:
                    for i in range(len(q_url_list)):
                        q2.put(q_url_list[i])
                l_name = ''.join(e.xpath('//em[@class="current"]/text()'))
                #获取下一页标签url
                next_page_list = e.xpath('//a[@class="athm-page__next"]/@href')
                if next_page_list:
                    next_url = next_page_list[0]
                    while True:
                        resp2 = requests.get('https://wenda.autohome.com.cn'+next_url,headers=headers)
                        e2 = etree.HTML(resp2.text)
                        # 每一页问题具体的url
                        q2_url_list = e2.xpath('//div[@class="question-list-wrapper"]/ul//h4/a/@href')
                        if q2_url_list:
                            for a in range(len(q2_url_list)):
                                q2.put(q2_url_list[a])
                        next2_page_list = e2.xpath('//a[@class="athm-page__next"]/@href')
                        if next2_page_list:
                            next_url = next2_page_list[0]
                            print('分析分页')
                        else:
                            break

            # print(q2.get())
            if q2.qsize() != 0:
                for i in range(10):
                    save_content(q2)
        except Exception:
            if q2.qsize() != 0:
                for i in range(15):
                    save_content(q2)
#解析具体页面
def save_content(q2):
    while not q2.empty():
        print('开始解析内容')
        url  = 'https://wenda.autohome.com.cn'+q2.get()
        resp = requests.get(url,headers=headers)
        resp.encoding='utf-8'
        e = etree.HTML(resp.text)
        #提问的问题
        ques = e.xpath('//h1[@class="card-title"]/text()')[0]
        #问题内容
        ques_content = e.xpath('//div[@ahe-role="text"][1]//p/text()')
        q_con = '无'
        if ques_content:
            q_con = ques_content[0]
        # 各级标签
        lve_name = e.xpath('//ul[@class="card-tag-list"]/li/text()')
        _name = '无'
        if lve_name:
            _name = ''.join(lve_name)
        #所有的评论div
        all_div  = e.xpath('//div[@class="card-reply-wrap"]')
        if all_div:
            for _div in all_div:
                all_c = _div.xpath('.//a[@class="text"]/@href')
                if all_c:
                    resp2 = requests.get('https://wenda.autohome.com.cn'+all_c[0],headers=headers)
                    resp2.encoding='utf-8'
                    e2 = etree.HTML(resp2.text)
                    #评论人的名字
                    re_name = e2.xpath('//a[@class="item reply-username"]/text()')[0]
                    #评论人的问答级别标签连接
                    img_list = e2.xpath('//span[@class="item flag-wrap"]/img/@src')
                    img_a = "无"
                    if img_list:
                        img_a = 'https://wenda.autohome.com.cn'+img_list[0]
                    #评论点赞人数
                    count = e2.xpath('//span[@class="time-wrap"]/text()')[0]
                    #评论的具体内容
                    con = ''.join(e2.xpath('//div[@class="answer-content"]//div[@ahe-role]/p/text()'))

                    with open('汽车之家问答_改进第二版.txt','a',encoding='utf-8') as f:
                        f.write('各级标签:%s'%_name+'\n')
                        f.write(ques+'\n')
                        f.write(q_con+'\n')
                        f.write(re_name+'\t'+'评论人的问答级别标签连接%s'%img_a+'\t'+count+'\n')
                        f.write(con+'\n')
                        f.write('-'*50+'\n')
                        f.flush()
        print(ques,'写入完成')


if __name__ == '__main__':
    #二三级标签url队列
    q = Queue()
    # #具体问题url队列
    q2 = Queue()
    # get_all_html(2,q)
    # all_html(q2,q)
    get1 = Thread(target=get_all_html,args=(1,q))
    get2 = Thread(target=get_all_html,args=(2,q))
    get3 = Thread(target=get_all_html,args=(3,q))
    # get4 = Thread(target=get_all_html,args=(4,q))
    get1.start()
    get2.start()
    # sleep(3)
    # all_1 = Thread(target=all_html,args=(q2,q))
    # all_1.start()
    get3.start()
    # get4.start()
    sleep(5)
    for i in range(10):
        all_t = Thread(target=all_html,args=(q2,q))
        # s = Thread(target=save_content,args=(q2,))
        all_t.start()
    # for a in range(50):
    # s.start()
    # all_html(q2,q)
    # save_content(q2)
    # save_content('https://wenda.autohome.com.cn/topic/detail/144357')