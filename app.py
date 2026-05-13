from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime 

app = Flask(__name__)
app.secret_key = "loti_slepeni_123" 

@app.before_request # Tas ir saraksts ar kura palīdzību ir pieejami tikai noteikti ceļi bez ielagošanās
def gatekeeper():
    publiskie_celi = ['sakums', 'registreties', 'login', 'static']
    
    if 'id' not in session and request.endpoint not in publiskie_celi:
        return redirect(url_for('login'))

@app.route("/") # Galvenā lapa, kas pieejama visiem lietotājiem
def sakums():
    return render_template("index.html")

@app.route("/registreties", methods=['GET', 'POST'])# Lietotāju reģistrācijas lapa - apstrādā datu ievadi un saglabā paroli un pārējos datus datubāzē 
def registreties():
    if request.method == 'POST':
        lietotajvards = request.form.get("lietotajs")
        epasts = request.form.get("epasts")
        parole_txt = request.form.get("parole")
        parole = generate_password_hash(parole_txt)
        
        conn = sqlite3.connect("projekta.db")
        c = conn.cursor()
        
        insert_sql = "INSERT INTO lietotaji (lietotajvards, parole, epasts) VALUES (?, ?, ?)"
        c.execute(insert_sql, (lietotajvards, parole, epasts))
        
        conn.commit()
        conn.close()
        return redirect(url_for('login'))

    return render_template("registreties.html")

@app.route("/pieteikties", methods=['GET', 'POST'])# Pieslēgšanās lapa - pārbauda lietotājvārdu un paroli no datubāzes, pieslēdzoties ir pieejamas parējās lapas
def login():
    if request.method == 'POST':
        lietotajs = request.form.get('lietotajs')
        parole = request.form.get('parole')

        conn = sqlite3.connect("projekta.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM lietotaji WHERE lietotajvards = ?", (lietotajs,))
        atbilde = c.fetchone()
        conn.close()

        if atbilde and check_password_hash(atbilde['parole'], parole):
            session["id"] = atbilde["id"]
            session["lietotajs"] = atbilde["lietotajvards"]
            session["epasts"] = atbilde["epasts"]
            return redirect(url_for('sakums'))
        else:
            return "Nepareizi dati!"

    return render_template("pieteikties.html")

@app.route("/iziet") # Izrakstīšanās maršruts - iziet ara no saites un novirza uz sākumu lapu.
def iziet():
    session.clear()
    return redirect(url_for('sakums'))

@app.route("/ienakosa_nauda", methods=['GET', 'POST'])# Ienākumu pievienošanas un apskates lapa - ļauj lietotājam reģistrēt ienākošo naudu, un redzēt lapā cik un kur patērēta nauda, tabulā kas atrodas lapas apakšdaļā
def ienakosa_nauda():
    lietotaja_id = session.get('id')

    if request.method == 'POST':
        summa = request.form.get("summa")
        avots = request.form.get("avots")
        sodien = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if summa and avots:
            conn = sqlite3.connect("projekta.db")
            c = conn.cursor()
            c.execute("""INSERT INTO Nauda (Lietotaji_id, veids, summa, iemesls, datums) 
                         VALUES (?, ?, ?, ?, ?)""", 
                      (lietotaja_id, 'ienakums', summa, avots, sodien))
            conn.commit()
            conn.close()
        return redirect(url_for('ienakosa_nauda'))

    conn = sqlite3.connect("projekta.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT summa, iemesls, datums FROM Nauda WHERE Lietotaji_id = ? AND veids = 'ienakums'", 
              (lietotaja_id,))
    visi_ienakumi = c.fetchall()
    conn.close()

    return render_template("ienakosa_nauda.html", ienakumi=visi_ienakumi)



@app.route("/patereta_nauda", methods=['GET', 'POST'])# Izdevumu pievienošanas un apskates lapa - ļauj lietotājam reģistrēt tēriņus, un redzēt kur un kāpēc terēts tabulā lapas apakšdaļā
def patereta_nauda():
    lietotaja_id = session.get('id')

    if request.method == 'POST':
        summa = request.form.get("summa")
        iemesls = request.form.get("iemesls")
        sodien = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if summa and iemesls:
            conn = sqlite3.connect("projekta.db")
            c = conn.cursor()
            c.execute("""INSERT INTO Nauda (Lietotaji_id, veids, summa, iemesls, datums) 
                         VALUES (?, ?, ?, ?, ?)""", 
                      (lietotaja_id, 'izdevums', summa, iemesls, sodien))
            conn.commit()
            conn.close()
        
        return redirect(url_for('patereta_nauda'))

    conn = sqlite3.connect("projekta.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT summa, iemesls, datums FROM Nauda WHERE Lietotaji_id = ? AND veids = 'izdevums'", 
              (lietotaja_id,))
    visi_izdevumi = c.fetchall()
    conn.close()

    return render_template("patereta_nauda.html", izdevumi=visi_izdevumi)

    conn = sqlite3.connect("projekta.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT summa, iemesls FROM izdevumi WHERE lietotaja_id = ?", (lietotaja_id,))
    visi_izdevumi = c.fetchall()
    conn.close()

    return render_template("patereta_nauda.html", izdevumi=visi_izdevumi)

@app.route("/pirkumu_vesture")# Visu darījumu vēsture - parāda sarakstu ar visiem ienākumiem un izdevumiem augošā secībā
def pirkumu_vesture():
    lietotaja_id = session.get('id')
    conn = sqlite3.connect("projekta.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT veids, summa, iemesls, datums FROM Nauda WHERE Lietotaji_id = ? ORDER BY datums DESC", (lietotaja_id,))
    visi_darijumi = c.fetchall()
    conn.close()
    return render_template("pirkumu_vesture.html", darijumi=visi_darijumi)

@app.route("/naudas_atlikums")# naudas atlikumu aprēķins - apreķina ienākošo naudu un patērēto naudas atlikumu un parāda tos tabulā 
def naudas_atlikums():
    lietotaja_id = session.get('id')
    
    conn = sqlite3.connect("projekta.db")
    c = conn.cursor()
    
    c.execute("SELECT SUM(summa) FROM Nauda WHERE Lietotaji_id = ? AND veids = 'ienakums'", (lietotaja_id,))
    kop_ienakumi = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(summa) FROM Nauda WHERE Lietotaji_id = ? AND veids = 'izdevums'", (lietotaja_id,))
    kop_izdevumi = c.fetchone()[0] or 0
    
    conn.close()
    
    bilance = kop_ienakumi - kop_izdevumi
    
    return render_template("naudas_atlikums.html", 
                           ienakumi=kop_ienakumi, 
                           izdevumi=kop_izdevumi, 
                           bilance=bilance)



if __name__ == "__main__":
    app.run(debug=True)