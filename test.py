import sqlite3
from flask import Flask, render_template, request, redirect, session, Response
import datetime
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'aquan'

def login_required(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        if session.get("username") != None:
            userna = session.get("username")
            print(f'{userna}')
            return func(*args, **kwargs)
        else:
            print(session.get("username"))
            resp = Response()
            resp.status_code = 200
            resp.data = "<script>window.location.href='/';</script>"
            return redirect('/')
    return wrapper

def adminlogin_required(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        if session.get("username") != None:
            userna = session.get("username")
            print(f'{userna}')
            return func(*args, **kwargs)
        else:
            print(session.get("username"))
            resp = Response()
            resp.status_code = 200
            resp.data = "<script>window.location.href='/admin-login';</script>"
            return redirect('/admin-login')
    return wrapper

@app.route("/logout",methods = ["GET","POST"])
@login_required
def logout():
    username = session.get("username")
    # 登出操作
    session.pop("username", None)
    session.pop("is_login", None)
    session.clear()
    return redirect('/')

@app.route("/admin-logout",methods = ["GET","POST"])
@adminlogin_required
def adminlogout():
    username = session.get("username")
    # 登出操作
    session.pop("username")
    session.pop("is_login")
    session.clear()
    return redirect('/admin-login')


# 定义错误处理函数
@app.errorhandler(404)
def handle_bad_request(error):
    return redirect('/error_page')  # 重定向到指定的网页


# 定义错误页面的路由
@app.route('/error_page')
def error_page():
    return render_template('404.html')  # 返回错误页面的模板

#连接数据库
def getconn():
    dbstr = "bookbook.db"
    conn = sqlite3.connect(dbstr)
    return conn

# 用户查询已借图书与状态
def querymybook(username):
    conn = getconn()
    cur = conn.cursor()
    #用户借了什么书
    recorde = cur.execute("select * from Bookstate where username=?", (username,)).fetchall()
    # recorde1 = cur.execute("select * from Book where number in "
    #                     "(select number from Bookstate where username=?)", (recorde[0][7],)).fetchall()
    #id,number,status,borrowtime,returntime,overtime,flag,username
    today = datetime.today()
    #书籍信息，借阅状态
    result = []
    result2 = []
    #for i in recorde:
    for i in range(len(recorde)):
        if recorde[i][4] != None:  # 归还时间不为空才继续执行，不然datetime.strptime会报错，且归还时间为空说明此书未借
            #超期
            if today > datetime.strptime(recorde[i][4], '%Y-%m-%d') and recorde[i][6] == 0:  # 将字符串格式化为日期，避免输入错误
                #一本书的信息
                recorde1 = cur.execute("select * from Book where number in "
                                       "(select number from Bookstate where username=? and number=?)",
                                       (recorde[i][7], recorde[i][1])).fetchall()
                flag = f",副本{recorde[i][0]},借书时间:{recorde[i][3]},归还期限:{recorde[i][4]}，已超期时间:{today - datetime.strptime(recorde[i][4], '%Y-%m-%d')}"
                result2.append(flag)
                result.append(recorde1)
                #一本书的信息
                print(f"图书信息：图书编号:{recorde1[0][0]},图书名字:{recorde1[0][1]},作者：{recorde1[0][2]},"
                      f"出版社：{recorde1[0][3]},出版时间：{recorde1[0][4]},价格：{recorde1[0][5]}")
                #时间
                print(
                    f",副本{recorde[i][0]},借书时间:{recorde[i][3]},归还期限:{recorde[i][4]}，已超期时间:{today - datetime.strptime(recorde[i][4], '%Y-%m-%d')}\n")
            else:
                recorde1 = cur.execute("select * from Book where number in "
                                       "(select number from Bookstate where username=? and number=?)",
                                       (recorde[i][7], recorde[i][1])).fetchall()
                flag = f",副本{recorde[i][0]},借书时间:{recorde[i][3]},归还期限:{recorde[i][4]}，未超期\n"
                result2.append(flag)
                result.append(recorde1)
                #(f"图书信息：图书编号:{recorde1[0][0]},图书名字:{recorde1[0][1]},作者：{recorde1[0][2]},"
                 #     f"出版社：{recorde1[0][3]},出版时间：{recorde1[0][4]},价格：{recorde1[0][5]}")
                #f",副本{recorde[i][0]},借书时间:{recorde[i][3]},归还期限:{recorde[i][4]}，未超期\n"
    if not recorde:
        result2.append('<script>alert("信息为空，还未借书")</script>')
        return result,result2
    else:
        return result,result2


# 查询任意用户借书状态
@app.route("/queryuser", methods=['GET', 'POST'])
@adminlogin_required
def queryuser():  # 管理员界面查询用户的借书状态
    if request.method == 'GET':
        return render_template('queryuser.html')
    if request.method == 'POST':
        conn = getconn()
        cur = conn.cursor()
        username = request.form.get('username')
        result,result2 = querymybook(username)
        if result != []:
            conn.commit()
            cur.close()
            return render_template('queryuser-show.html',data = result,data2 = result2)
        else:
            conn.commit()
            cur.close()
            return render_template('queryuser.html') + '<script>alert("信息为空，还未借书")</script>'


# 管理员查询图书状态
def querycopy(number):
    conn = getconn()
    cur = conn.cursor()
    recorde = cur.execute(f"select * from Bookstate where Bookstate.number = {number}").fetchall()
    num = 0
    for i in recorde:  # 计算图书还有多少副本可以借
        if i[6] == 1:
            num += 1
    if num == 0:
        print(f"编号为{number}的书,不在库,没有副本可以借")
        cur.close()
        result = [f"编号为{number}的书,不在库,没有副本可以借"]
        return result
    else:
        print(f"编号为{number}的书,在库,还有{num}个副本可以借")
        result = []
        result.append(f"编号为" + str(number) +"的书,在库,还有" +str(num) + "个副本可以借")
        j = 3
        today = datetime.today()
        for i in recorde:
            if i[4] != None:  # 归还时间不为空才继续执行，不然datetime.strptime会报错
                if i[0] == 1:
                    if today > datetime.strptime(i[4], '%Y-%m-%d') and i[6] == 0:  # 将字符串格式化为日期，避免输入错误
                        print(
                            f"副本{1},借书时间:{i[3]},归还期限{i[4]}，已超期时间:{today - datetime.strptime(i[4], '%Y-%m-%d')}")
                        result.append(f"副本{1},借书时间:{i[3]},归还期限{i[4]}，已超期时间:{today - datetime.strptime(i[4], '%Y-%m-%d')}")
                    else:
                        print(f"副本{1},借书时间:{i[3]},归还期限{i[4]}，未超期")
                        result.append(f"副本{1},借书时间:{i[3]},归还期限{i[4]}，未超期")
                else:
                    if today > datetime.strptime(i[4], '%Y-%m-%d') and i[6] == 0:  # 将字符串格式化为日期，避免输入错误
                        print(
                            f"副本{2},借书时间:{i[3]},归还期限{i[4]}，已超期时间:{today - datetime.strptime(i[4], '%Y-%m-%d')}")
                        result.append(f"副本{1},借书时间:{i[3]},归还期限{i[4]}，未超期")
                    else:
                        print(f"副本{2},借书时间:{i[3]},归还期限{i[4]}，未超期")
                        result.append(f"副本{2},借书时间:{i[3]},归还期限{i[4]}，未超期")
        cur.close()
        return result

#显示信息
def showall():
    conn = getconn()
    cur = conn.cursor()
    recorde = cur.execute("select * from Book").fetchall()
    result = []
    for re in recorde:
        print(re)
        s = querycopy(re[0])
        result.append(s)
        ##recorde=cur.execute("select * from Bookstate where Bookstate.number = Book.number").fetchall()
    cur.close()
    return recorde,result


#获取书籍完整信息
def getdata():
    udbooknum = request.form.get('book_number1')
    a = request.form.get('book_number')
    b = request.form.get('book_name')
    c = request.form.get('book_author')
    d = request.form.get('book_press')
    e = request.form.get('book_pubdate')
    f = request.form.get('book_price')
    if udbooknum ==None:
        return a,b,c,d,e,f
    else:
        return udbooknum,a,b,c,d,e,f

#获取编号或名称
def getdatadel():
    a = request.form.get('book_number')
    b = request.form.get('book_name')
    return a,b

# 添加书籍
@app.route("/addbook",methods=['GET','POST'])
@adminlogin_required
def addbook():
    if request.method == 'GET':
        return render_template('addbook.html')
    if request.method == 'POST':
        #获取输入
        a,b,c,d,e,f = getdata()
        print(a,b,c,d,e,f)
        conn = getconn()
        cur = conn.cursor()

        cur.execute("SELECT  number  FROM  Book  WHERE  number  = ?", (a,))  # 查询编号是否存在
        if cur.fetchone() is not None:
            conn.commit()
            cur.close()
            return render_template('addbook.html') + f'<script>alert("{a}已经存在，无法添加")</script>'

        if a != None:
            # records = getdata()
            sqlstr = "insert into Book (number,name,author,press,pubdate,price)" \
                     "values(?,?,?,?,?,?)"
            # 每本书3个副本
            cur.execute(sqlstr, (a, b, c, d, e, f))
            cur.execute(f"insert into Bookstate(id,number) values(1,{a})")
            cur.execute(f"insert into Bookstate(id,number) values(2,{a})")
            cur.execute(f"insert into Bookstate(id,number) values(3,{a})")
            print("插入成功！")
            conn.commit()
            cur.close()
            return redirect('/admin')





#删除图书
@app.route("/delbook",methods=['GET','POST'])
@adminlogin_required
def delbook():
    if request.method == 'GET':
        return render_template('delbook.html')
    if request.method == 'POST':
        conn = getconn()
        cur = conn.cursor()
        a,b = getdatadel()
        #a = request.form.get('book_number')
        #b = request.form.get('book_name')
        print(a,b)
        if a != None:
            num = a
            cur.execute("select * from Book where number=:num", {"num": num})
            record = cur.fetchall()
            for line in record:
                print(line)
            cur.execute("delete from Book where number=:num", {"num": num})
            cur.execute("delete from Bookstate where number=:num", {"num": num})
        if b != None:
            name = b
            #elif op == '书名':
            cur.execute("select * from Book where name=:name", {"name": name})
            record = cur.fetchall()
            for line in record:
                print(line)
            cur.execute("delete from Bookstate where number in(select number from Book where name=:name)",
                        {"name": name})
            cur.execute("delete from Book where name=:name", {"name": name})
        #该图书删除成功
        conn.commit()
        cur.close()
        if a!=None:
            return render_template('delbook.html') + f'<script>alert("{a}删除成功")</script>'
        if b!=None:
            return render_template('delbook.html') + f'<script>alert("{b}删除成功")</script>'

#修改图书
@app.route("/udbook", methods=['GET', 'POST'])
@adminlogin_required
def udbook():
    if request.method == 'GET':
        return render_template('udbook.html')
    if request.method == 'POST':
        conn = getconn()
        cur = conn.cursor()
        #原编号，编号.....
        num,a, b, c, d, e, f = getdata()
        #检查是否编号重复
        cur.execute("SELECT  number  FROM  Book  WHERE  number  = ? AND number != ?", (a,num,))  # 查询编号是否存在
        if cur.fetchone() is not None:
            print("该编号已使用,添加失败")
            conn.commit()
            cur.close()
            return  render_template('udbook.html') + f'<script>alert("已经存在编号{a}")</script>'
        #num = input("请输入图书编号：")
        row = cur.execute("select * from Book where number=?", (num,)).fetchall()
        if not row:
            conn.commit()
            cur.close()
            return render_template('udbook.html') + '<script>alert("不存在该书")</script>'

        else:
            print(2222)
            #a,b,c,d,e,f = getdata()
            sqlstr = "update Book set number=?,author=?,press=?,pubdate=?,price=? where number=?"
            cur.execute(sqlstr, (a,c,d,e,f,num))
            sqlstr = "update Bookstate set number=? where number=?"
            cur.execute(sqlstr, (a, num))
            print("修改成功")
            conn.commit()
            cur.close()
            return redirect('/admin')


#查询某本图书信息和状态
@app.route("/queryms", methods=['GET', 'POST'])
@adminlogin_required
def queryms():
    if request.method == 'GET':
        #输入
        return render_template('queryms.html')
    if request.method == 'POST':
        conn = getconn()
        cur = conn.cursor()
        #op = querybook()  # 查询图书信息
        #a=book_number,b=book_name
        a,b = getdatadel()
        if a != None:
            num = a
            cur.execute("select * from Book where number=:num", {"num": num})
            record = cur.fetchall()
            print(record)
            if record == []:
                cur.close()
                return render_template('queryms.html', data=record) + '<script>alert("该编号不存在")</script>'
            else:
                result = querycopy(a)
                cur.close()
                return render_template('queryms-show.html', data=record,result=result)
        elif b != None:
            name = b
            #cur.execute("select * from Book where name=?", {"name": name})
            record = cur.execute("select * from Book where name =?", (b,)).fetchall()
            #record = cur.fetchall()
            if record == []:
                cur.close()
                return render_template('queryms.html', data=record) + '<script>alert("该编号不存在")</script>'
            else:
                a = record[0]
                print(record)
                print(a[0],1111)
                result = querycopy(a[0])
                cur.close()
                return render_template('queryms-show.html', data=record,result=result)

@app.route("/query-all-records", methods=['GET', 'POST'])
@adminlogin_required
def query_all_records():
    if request.method == 'GET':
        conn = getconn()
        cur = conn.cursor()
        cur.execute("select * from Record")
        records = cur.fetchall()
        return render_template('/query-all-records.html',data=records)




########################################x下面为用户操作，上面为管理员的操作

#查询某本图书信息和状态
@app.route("/userqueryms/<string:flaggg>", methods=['GET', 'POST'])
@login_required
def userqueryms(flaggg):
    if request.method == 'GET':
        #输入
        return render_template('user-queryms.html',flaggg=flaggg)
    if request.method == 'POST':
        conn = getconn()
        cur = conn.cursor()
        #op = querybook()  # 查询图书信息
        #a=book_number,b=book_name
        a,b = getdatadel()
        if a != None:
            num = a
            cur.execute("select * from Book where number=:num", {"num": num})
            record = cur.fetchall()
            print(record)
            if record == []:
                cur.close()
                return render_template('user-queryms.html', data=record,flaggg=flaggg) + '<script>alert("该编号不存在")</script>'
            else:
                result = querycopy(a)
                cur.close()
                return render_template('user-queryms-show.html', data=record,result=result,flaggg=flaggg)
        elif b != None:
            name = b
            #cur.execute("select * from Book where name=?", {"name": name})
            record = cur.execute("select * from Book where name =?", (b,)).fetchall()
            #record = cur.fetchall()
            if record == []:
                cur.close()
                return render_template('user-queryms.html', data=record,flaggg=flaggg) + '<script>alert("该书名不存在")</script>'
            else:
                a = record[0]
                print(record)
                print(a[0],1111)
                result = querycopy(a[0])
                cur.close()
                return render_template('user-queryms-show.html', data=record,result=result,flaggg=flaggg)

#################借书

def overtime(username):  # 判断是否有超期图书未归还
    conn = getconn()
    cur = conn.cursor()
    recorde = cur.execute("select * from Bookstate where username=?", (username,)).fetchall()
    if not recorde:
        conn.commit()
        cur.close()
        return 0  # 如果一条记录都没有，说明还未借书，也就没有超期图书
    today = datetime.today()
    has_overdue = False
    for i in recorde:
        if i[4] != None:  # 归还时间不为空才继续执行，不然datetime.strptime会报错
            if today > datetime.strptime(i[4], '%Y-%m-%d') and i[6] == 0:  # 将字符串格式化为日期，避免输入错误
                recorde1 = cur.execute("select number,name from Book where number in "
                                       "(select number from Bookstate where username=? and number=?)",
                                       (i[7], i[1])).fetchall()
                print(f"图书编号:{recorde1[0][0]},图书名字:{recorde1[0][1]},副本{i[0]},借书时间:{i[3]},归还期限:{i[4]}，"
                      f"已超期时间:{today - datetime.strptime(i[4], '%Y-%m-%d')}")
                has_overdue = True
    cur.close()
    return 1 if has_overdue else 0


#借书
@app.route("/borrowbook/<string:username>",methods=['GET','POST'])
@login_required
def borrowbook(username):  # user登录时的账号，在借书时使用此账号
    if request.method == 'GET':
        return render_template('user-borrowbook.html',flaggg=username)
    if request.method == 'POST':
        conn = getconn()
        cur = conn.cursor()
        a,b = getdatadel()    #读取操作
        #a = request.form.get('book_num')
        #b = request.form.get('book_name')
        c = request.form.get('time')
        d = request.form.get('time1')
        ov = overtime(username)    #检验是否有借书资格
        if ov == 1:
            print(f"你有超期图书未归还，请归还后才能借阅")
            # 有超期图书不能借书
            conn.commit()
            cur.close()
            return render_template('user-borrowbook.html',flaggg=username) + '<script>alert("你有超期图书未归还，请归还后才能借阅")</script>'
        row = cur.execute("select count(*) as count1 from Bookstate where username=?", (username,)).fetchone()
        count = row[0]
        if count >= 2:
            conn.commit()
            cur.close()
            return render_template('user-borrowbook.html',flaggg=username) + '<script>alert("对不起，一个账号一次只能借阅两本书，你已经达到数量上限")</script>'
        if a != None:
            number = a
            recorde = cur.execute("select * from Book where number=?", (number,)).fetchall()
            recorde = cur.execute("select * from Bookstate where number = ? and status='在库'", (number,)).fetchall()
            if not recorde:
                conn.commit()
                cur.close()
                return render_template('user-borrowbook.html',flaggg=username) + '<script>alert("该书已经没有副本可以借阅，请选择其他书籍")</script>'
            else:
                #应该调用时间函数获取当前的时间，
                borrowtime = c
                returntime = (datetime.strptime(borrowtime, '%Y-%m-%d') + timedelta(days=60)).strftime('%Y-%m-%d')
                sqlstr = "update Bookstate set status=?, borrowtime=?,returntime=?,flag=0,username=? " \
                         "where id=? and number=?"
                cur.execute(sqlstr, ("不在库", borrowtime, returntime, username, recorde[0][0], number))
                conn.commit()
                cur.close()
                return render_template('user-borrowbook.html',flaggg=username) + '<script>alert("借阅成功")</script>'
        elif b != None:
            name = b
            recorde = cur.execute("select * from Book where name=?", (name,)).fetchall()
            recorde = cur.execute(
                "select * from Bookstate where number in(select number from Book where name=?) and status='在库'",
                (name,)).fetchall()
            if not recorde:
                conn.commit()
                cur.close()
                return render_template('user-borrowbook.html',flaggg=username) + '<script>alert("该书已经没有副本可以借阅，请选择其他书籍")</script>'
            else:
                number = recorde[0][1]
                borrowtime = d
                returntime = (datetime.strptime(borrowtime, '%Y-%m-%d') + timedelta(days=60)).strftime('%Y-%m-%d')
                sqlstr = "update Bookstate set status=?, borrowtime=?,returntime=?,flag=0,username=? " \
                         "where id=? and number=?"
                cur.execute(sqlstr, ("不在库", borrowtime, returntime, username, recorde[0][0], number))
                conn.commit()
                cur.close()
                return render_template('user-borrowbook.html', flaggg=username) + '<script>alert("借阅成功")</script>'



# 还书
@app.route("/returnbook/<username>",methods=['GET','POST'])
@login_required
def returnbook(username):
    if request.method == 'GET':
        return render_template('user-returnbook.html',flaggg=username)
    if request.method == 'POST':
        conn = getconn()
        cur = conn.cursor()
        #书本信息，借阅信息
        result,result2 = querymybook(username)
        if result == []:
            conn.commit()
            cur.close()
            return render_template('user-returnbook.html',flaggg=username) + '<script>alert("你还没有借书，无法还书！")</script>'
        #编号，副本编号
        a,b = getdatadel()
        number = a
        id = b
        # 获取当前借书记录
        record = cur.execute("select borrowtime, returntime from Bookstate where number=? and id=? and username=?",
                             (number, id, username)).fetchone()
        if record:
            borrowtime, returntime = record
            # 插入到Record表中
            cur.execute("insert into Record (number, id, username, outtime, intime) values (?, ?, ?, ?, ?)",
                        (number, id, username, borrowtime, datetime.today().strftime('%Y-%m-%d')))

            # 更新Bookstate表
            sqlstr = "update Bookstate set status=?, borrowtime=?, returntime=?, flag=?, username=? where number=? and id=? and username=?"
            cur.execute(sqlstr, ('在库', None, None, 1, None, number, id, username))
            conn.commit()
            cur.close()
            return render_template('user-returnbook.html',flaggg=username) + '<script>alert("还书成功")</script>'
        else:
            conn.commit()
            cur.close()
            return render_template('user-returnbook.html',flaggg=username) + '<script>alert("未查到对应书籍，有问题请找管理员")</script>'



#用户查询历史
@app.route("/query_record",methods=['GET','POST'])
@login_required
def query_record():
    if request.method == 'GET':
        conn = getconn()
        cur = conn.cursor()
        username = session.get("username")
        cur.execute("select * from Record where username=:user", {"user": username})
        records = cur.fetchall()
        for record in records:
            print(record)
        return render_template('query-record.html',data=records,flaggg = session.get("username"))






#登录界面
@app.route("/admin-login",methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    #获取输入的账号密码
    user = request.form.get('user')
    pwd = request.form.get('pwd')
    #连接数据库
    conn = getconn()
    cur = conn.cursor()
    row = cur.execute("select * from manager where username=? and password=?", (user, pwd)).fetchone()
    if row is not None:
        session["username"] = user
        session["is_login"] = True
        conn.commit()
        cur.close()
        return redirect('/admin')
    else:
        conn.commit()
        cur.close()
        return render_template('login.html') + '<script>alert("账号密码错误")</script>'

#管理员
@app.route("/admin",methods=['GET','POST'])
@adminlogin_required
def admin():
    if request.method == 'GET':
        #admin操作界面
        return render_template('admin-op.html')
    #获取操作
    op = request.form.get('op')
    #if op == '1':
       # return render_template('admin.html',op=op)
    if op == '0':
        return redirect("/admin-logout")
    elif op == '1':
        return redirect("/addbook")
    elif op == '2':
        return redirect("/delbook")
    elif op == '3':
        return redirect("/udbook")
    elif op == '4':
        return redirect("/queryms")
    elif op == '5':
        return redirect("/queryuser")
    elif op == '6':
        recorde,result = showall()
        return render_template('showall.html', data=recorde,result=result)
    elif op == '7':
        return redirect('/query-all-records')
        #query_all_records()
    else:
        #无效操作
        return render_template('admin-op.html') + '<script>alert("操作不存在")</script>'



#用户登录界面
@app.route("/",methods=['GET','POST'])
def userlogin():
    if request.method == 'GET':
        return render_template('user-login.html')
    #获取输入的账号密码
    user = request.form.get('user')
    pwd = request.form.get('pwd')
    #连接数据库
    conn = getconn()
    cur = conn.cursor()
    row = cur.execute("select * from Login where username=? and password=?", (user, pwd)).fetchone()
    if row is not None:
        session["username"] = user
        session["is_login"] = True
        conn.commit()
        cur.close()
        return redirect(f"/user/{user}")
    else:
        conn.commit()
        cur.close()
        return render_template('user-login.html') + '<script>alert("账号密码错误")</script>'



#用户操作
@app.route("/user/<username>",methods=['GET','POST'])
@login_required
def user(username):
    if request.method == 'GET':
        #用户操作界面
        return render_template('user-op.html')
    op = request.form.get('op')
    username = session["username"]
    #用户选择操作
    if op == '0':
        return redirect('/logout')
    elif op == '1':
        return redirect(f'/borrowbook/{username}')
    elif op == '2':
        return redirect(f'/returnbook/{username}')
    elif op == '3':
        return redirect(f'/userqueryms/{username}')

    elif op == '4':
        result, result2 = querymybook(username)
        if result != []:
            return render_template('user-queryuser-show.html', data=result, data2=result2,flaggg=username)
        else:
            return render_template('user-op.html',flaggg=username) + '<script>alert("信息为空，还未借书")</script>'
    elif op == '5':
        #query_record(op[1])
        return redirect(f'/query_record')

    else:
        return render_template('user-op.html') + '<script>alert("操作不存在")</script>'

#用户注册
@app.route("/register",methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('user-register.html')
    if request.method == 'POST':
        user = request.form.get('user')
        pwd = request.form.get('pwd')
        # 连接数据库
        conn = getconn()
        cur = conn.cursor()
        #判断是否被注册过
        cur.execute("SELECT  username  FROM  Login  WHERE  username  =  ?", (user,))
        if cur.fetchone() is not None:
            conn.commit()
            cur.close()
            return render_template('user-register.html') + '<script>alert("该账号已经被注册，无法注册")</script>'
        cur.execute("insert into Login(username,password) values(?,?)", (user, pwd))
        conn.commit()
        cur.close()
        return render_template('user-register.html') + '<script>alert("注册成功")</script>'






###################################







if __name__=='__main__':
    app.run()

