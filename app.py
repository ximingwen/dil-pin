import flask
from flask import Flask, redirect, url_for, request,session, jsonify
from datetime import datetime
import re, sys,os, json
from flask import render_template
import Pinterest
import urllib.request as req
from flask_fontawesome import FontAwesome
# import vision_functions
import os


app = Flask(__name__)
app.secret_key = os.urandom(12)



@app.route("/")
def index():
    return render_template("login.html")


@app.route('/login', methods=['POST', 'GET'])
def login(data=None):
    if request.method == 'POST':
        user = request.form['username']
        email=request.form['email']
        pw = request.form['password']
        # print(user, file=sys.stdout)
        pint = Pinterest.Pinterest(username=user,email=email, password=pw)
        flask.current_app.account= pint
        login_sts= pint.login()
        # print(login_sts.status_code, file=sys.stdout)
        # print(pint.get_user_overview(), file=sys.stdout)
        # print(flask.current_app.account)

        user_info= pint.get_user_overview()
        flask.current_app.user_info= user_info

        if(login_sts.status_code==200):
            session['username']=user
            session['password']=pw
            session['email']=email
            return render_template("user.html",data=user_info)
        else:
            return redirect(url_for('login'))

    if request.method == 'GET':
        
        query = flask.request.args.get('query')
        # current_account = flask.g.get('current')
        current_account=flask.current_app.account
        # print(current_account)
        res = []
        search_batch = current_account.search('pins', query)
        while len(search_batch) > 0 and len(res) < 250:
            res += search_batch
            search_batch = current_account.search('pins', query=query)
        # res=current_account.search('pins',query)
        with open(str(query)+'.json', 'w') as f:
            json.dump(res, f)

        return flask.jsonify(res)

@app.route('/download', methods=['POST', 'GET'])
def download():
    if request.method == 'POST':
        query = request.form['query']
        imgs = request.form.getlist('doc_imgs[]')

        path=query

        
        user_name = flask.current_app.user_info['username']

        print("now entering the download path")

        # print(request.form)
        # print(user_name)

        if not os.path.exists('Pics'):
            os.mkdir('Pics')
        
        if not os.path.exists('Pics/'+user_name+query):
            os.mkdir('Pics/'+user_name+'_'+query)
        
        print('downloading pictures')
        for i in imgs:
            img_name=re.search(pattern='[0-9a-z]*.jpg',string=i).group()
            # print('/'+path+'/'+img_name)  
            req.urlretrieve(i, 'Pics/'+user_name+'_'+query+'/'+img_name)
        print('download succes')
        return  "susscess"


@app.route('/account', methods=['POST', 'GET'])
def account():
    if request.method == 'GET':
        user_info = flask.current_app.user_info

        with open(user_info['username']+'.json', 'w') as f:
            json.dump(user_info, f)
    return "success"
    
@app.route('/analysis', methods=['POST','GET'])
def analysis():
        if request.method == 'GET':
            dirs=os.listdir('Pics')
            return render_template('analysis.html',data=dirs)


@app.route('/get_folder', methods=['GET'])
def get_folder():
     if request.method == 'GET':
         
         folder = flask.request.args.get('name')
         folder= folder.strip()
         res={}
         res['summary']=os.stat('Pics/'+folder)
         res['array']=os.listdir('Pics/'+folder)
         flask.current_app.folder_name = folder

        # So the variable res['array'] contains all the file names you need to use.
        # You could continue coding from here
        # This method should generate things that could possibly return to the html page (analysis.html)


         return jsonify(result=res)

# ANALYSIS BUTTON
@app.route('/get_image_pngs_json', methods=['GET'])
def get_image_pngs_json():
    if request.method == 'GET':
        STOP_WORDS = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',"you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself','yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her','hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them','their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom','this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are','was', 'were', 'be', 'been', 'being', 'have', 'has', 'had','having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and','but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at','by', 'for', 'with', 'about', 'against', 'between', 'into','through', 'during', 'before', 'after', 'above', 'below', 'to','from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under','again', 'further', 'then', 'once', 'here', 'there', 'when','where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more','most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own','same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will','just', 'don', "don't", 'should', "should've", 'now', 'd', 'll','m', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn',"couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't",'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma','mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't",'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't",'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"]
        FOLDER_NAME = flask.current_app.folder_name

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="Google_vision_API/pinterest-service.json"
        print(str(FOLDER_NAME) + ' FOLDER NAME')

        SEARCH_TERM= str(re.split('_', FOLDER_NAME)[1])
        print(SEARCH_TERM + ' SEARCH TERM')

        # make list of image paths
        img_paths = []

        MAX = 15
        i = 1
        directory = os.fsencode('Pics/' + FOLDER_NAME)
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            if (filename.endswith(".jpg") & (i <= MAX)): 
                img_str = 'Pics/' + FOLDER_NAME+ '/'+ str(filename)
                img_paths.append(img_str)
                i = i +1

        print(len(img_paths))
        print('paths gathered')

        # LABEL WORDCLOUD
        label_lists = vision_functions.get_label_lists(img_paths)
        wordcloud = vision_functions.get_wordcloud(label_lists, SEARCH_TERM)
        wordcloud.to_file('image_outputs/label_wordcloud_' + SEARCH_TERM + '.png')
        print('label_wordcloud saved')

        # DESCRIPTION WORDCLOUD
        json_path = SEARCH_TERM + '.json'
        json_dict = vision_functions.get_json_dict(json_path)
        descripts = vision_functions.get_descripts(json_dict)
        STOP_WORDS.append(SEARCH_TERM)
        wordcloud = vision_functions.get_desc_wordcloud(descripts, STOP_WORDS)
        wordcloud.to_file('image_outputs/description_wordcloud_' + SEARCH_TERM + '.png')
        print('decription_wordcloud saved')

        # DOMAIN WORDCLOUD
        domains = vision_functions.get_domains(json_dict)
        wordcloud = vision_functions.get_wordcloud(domains, SEARCH_TERM)
        wordcloud.to_file('image_outputs/domian_wordcloud_' + SEARCH_TERM + '.png')
        print('domain_wordcloud saved')

        # BOARD WORDCLOUD
        boards = vision_functions.get_boards(json_dict)
        wordcloud = vision_functions.get_wordcloud(boards, SEARCH_TERM)
        wordcloud.to_file('image_outputs/board_wordcloud_' + SEARCH_TERM + '.png')
        print('board_wordcloud saved')

        # PROMOTER WORDCLOUD
        promoters = vision_functions.get_promoters(json_dict)
        wordcloud = vision_functions.get_wordcloud(promoters, SEARCH_TERM)
        wordcloud.to_file('image_outputs/promoter_wordcloud_' + SEARCH_TERM + '.png')
        print('promoter_wordcloud saved')

        # CREATED AT GRAPH
        #dates = vision_functions.get_dates(json_dict)
        #date_graph = vision_functions.get_date_graph(dates)
        #date_graph.to_file('date_graph.png')
        #print('date graph saved')

        # LABEL COSSIM
        vectors = vision_functions.get_label_vectors(label_lists)
        avg_cossim = str(vision_functions.get_avg_cosine_sim(vectors))
        text_file = open(("image_outputs/cossim_" + SEARCH_TERM + ".txt"), "w")
        text_file.write("Average Cossine Similarity: %s" % avg_cossim)
        text_file.close()
        print('cossim saved')

        # DETECT COLOR PROPERTIES
        df_list = []
        for path in img_paths:
            df_list.append(vision_functions.get_properties_df(path))

        prop_json = str(vision_functions.get_properties_json(df_list))
        intro_str = """Highcharts.chart('container', {chart: {type: 'packedbubble',height: '80%'},title: {text: 'Simple packed bubble'},tooltip: {useHTML: true,pointFormat: '<b>{point.name}:</b> {point.y}</sub>'},plotOptions: {packedbubble: {dataLabels: {enabled: true,format: '{point.name}',style: {color: 'black',textOutline: 'none',fontWeight: 'normal'}},minPointSize: 0}},series: ["""
        full_str = intro_str + prop_json + ']});'
        text_file = open(("image_outputs/prop_json_" + SEARCH_TERM + ".js"), "w")
        text_file.write(full_str)
        text_file.close()
        print('properties json saved')
        return ('objects saved')





if __name__ == '__main__':
    from werkzeug.serving import WSGIRequestHandler
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(host="0.0.0.0", port=8080, debug=True,use_reloader=True)