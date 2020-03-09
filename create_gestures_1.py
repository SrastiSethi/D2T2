#!/usr/bin/env python
import cv2 as cv
import numpy as np
import pickle, os, sqlite3, random

image_x, image_y = 50, 50

def get_hand_hist():
	with open("hist", "rb") as f: #read binary #opening file
		hist = pickle.load(f) #loading f obj in hist
	return hist

def init_create_folder_database():
	# create the folder and database if not exist
	if not os.path.exists("gestures"): #path name
		os.mkdir("gestures")
	if not os.path.exists("gesture_db.db"):
		conn = sqlite3.connect("gesture_db.db")
		create_table_cmd = "CREATE TABLE gesture ( g_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, g_name TEXT NOT NULL )"
		conn.execute(create_table_cmd)
		conn.commit()

def create_folder(folder_name):
	if not os.path.exists(folder_name):
		os.mkdir(folder_name)

def store_in_db(g_id, g_name):
	conn = sqlite3.connect("gesture_db.db")
	cmd = "INSERT INTO gesture (g_id, g_name) VALUES (%s, \'%s\')" % (g_id, g_name)
	try:
		conn.execute(cmd)
	except sqlite3.IntegrityError:
		choice = input("g_id already exists. Want to change the record? (y/n): ")
		if choice.lower() == 'y':
			cmd = "UPDATE gesture SET g_name = \'%s\' WHERE g_id = %s" % (g_name, g_id)
			conn.execute(cmd)
		else:
			print("Doing nothing...")
			return
	conn.commit()
	
def store_images(g_id):
	total_pics = 1200
	hist = get_hand_hist()
	cam = cv.VideoCapture(0)
	if cam.read()[0]==False:
		cam = cv.VideoCapture(0)
	x, y, w, h = 300, 100, 300, 300

	create_folder("gestures/"+str(g_id))
	pic_no = 0
	flag_start_capturing = False
	frames = 0
	
	while True:
		img = cam.read()[1]
		img = cv.flip(img, 1)
		imgHSV = cv.cvtColor(img, cv.COLOR_BGR2HSV)
		dst = cv.calcBackProject([imgHSV], [0, 1], hist, [0, 180, 0, 256], 1)
		disc = cv.getStructuringElement(cv.MORPH_ELLIPSE,(10,10))
		cv.filter2D(dst,-1,disc,dst)
		blur = cv.GaussianBlur(dst, (11,11), 0)
		blur = cv.medianBlur(blur, 15)
		thresh = cv.threshold(blur,0,255,cv.THRESH_BINARY+cv.THRESH_OTSU)[1]
		thresh = cv.merge((thresh,thresh,thresh))
		thresh = cv.cvtColor(thresh, cv.COLOR_BGR2GRAY)
		thresh = thresh[y:y+h, x:x+w]
		contours, hierarchy = cv.findContours(thresh.copy(), cv.RETR_TREE, cv.CHAIN_APPROX_NONE)



		if len(contours) > 0:
			contour = max(contours, key = cv.contourArea)
			if cv.contourArea(contour) > 10000 and frames > 50:
				x1, y1, w1, h1 = cv.boundingRect(contour)
				pic_no += 1
				save_img = thresh[y1:y1+h1, x1:x1+w1]
				if w1 > h1:
					save_img = cv.copyMakeBorder(save_img, int((w1-h1)/2) , int((w1-h1)/2) , 0, 0, cv.BORDER_CONSTANT, (0, 0, 0))
				elif h1 > w1:
					save_img = cv.copyMakeBorder(save_img, 0, 0, int((h1-w1)/2) , int((h1-w1)/2) , cv.BORDER_CONSTANT, (0, 0, 0))
				save_img = cv.resize(save_img, (image_x, image_y))
				rand = random.randint(0, 10)
				if rand % 2 == 0:
					save_img = cv.flip(save_img, 1)
				cv.putText(img, "Capturing...", (30, 60), cv.FONT_HERSHEY_TRIPLEX, 2, (127, 255, 255))
				cv.imwrite("gestures/"+str(g_id)+"/"+str(pic_no)+".jpg", save_img)

		cv.rectangle(img, (x,y), (x+w, y+h), (0,255,0), 2)
		cv.putText(img, str(pic_no), (30, 400), cv.FONT_HERSHEY_TRIPLEX, 1.5, (127, 127, 255))
		cv.imshow("Capturing gesture", img)
		cv.imshow("thresh", thresh)
		keypress = cv.waitKey(1)
		if keypress == ord('c'):
			if flag_start_capturing == False:
				flag_start_capturing = True
			else:
				flag_start_capturing = False
				frames = 0
		if flag_start_capturing == True:
			frames += 1
		if pic_no == total_pics:
			break

init_create_folder_database()
g_id = input("Enter gesture no.: ")
g_name = input("Enter gesture name/text: ")
store_in_db(g_id, g_name)
store_images(g_id)
