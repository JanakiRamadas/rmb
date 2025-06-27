from flask import Flask, request, url_for, redirect, session, render_template, json, flash, send_file, jsonify
from flask_session import Session


import requests
from urllib.request import urlopen
import json


ServerBank = Flask(__name__)
ServerBank.config["SESSION_PERMANENT"] = False
ServerBank.config["SESSION_TYPE"] = "filesystem"
ServerBank.config['SECRET_KEY'] = b'1db9a6ffaf6a8566338d6d2f8db1f812a7c23a4e25299ab6ab228a81e9cfdaf0'
Session(ServerBank)
Session(ServerBank)





	



@ServerBank.route('/show_cminer_invoice', methods=['GET', 'POST'])
def show_cminer_invoice():
	if request.method == 'POST':
		if request.form['submit_button'] == 'Download zip':
			zipname = request.form['zipname']
			zipname = zipname+'.zip'
			with zipfile.ZipFile(zipname,'w',  zipfile.ZIP_DEFLATED) as zip:
					zip.write(session['pdffile_with_path'])
			zip.close()
			return send_file(zipname)
		if request.form['submit_button'] == 'Exit':
			return '%s' %'Thanks'
		if request.form['submit_button'] == 'Send mail':
			send_the_mail(session['cminer_email'], session['pdffile_with_path'], session['messtext'], session['mess_subject'] )
	return render_template('show_cminer_invoice.html')







if __name__ == '__main__':
	#from waitress import serve
	#import logging
	#print("ServerBank is now running through Waitress WSGI")
	#serve(ServerBank, host="0.0.0.0", port=443)

	#ServerBank.run(host='0.0.0.0', port=5002, debug = True)
	ServerBank.run(debug=True)



