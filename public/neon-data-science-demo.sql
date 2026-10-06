-- FaceTrack clean Data Science demo seed
-- Keeps the existing admin account. Removes old attendance, faces, timetable, classes, teachers and students.
BEGIN;
DELETE FROM attendance_corrections;
DELETE FROM attendance_marks;
DELETE FROM attendance_sessions;
DELETE FROM face_descriptors;
DELETE FROM timetable;
DELETE FROM teacher_assignments;
DELETE FROM users WHERE role <> 'admin';
DELETE FROM classes;
DELETE FROM departments;

INSERT INTO departments(name) VALUES ('B.Sc Data Science'), ('M.Sc Data Science');

INSERT INTO classes(name,dept_id,semester) VALUES
('B.Sc Data Science - 1st Year - Semester 1',(SELECT id FROM departments WHERE name='B.Sc Data Science'),1),
('B.Sc Data Science - 1st Year - Semester 2',(SELECT id FROM departments WHERE name='B.Sc Data Science'),2),
('B.Sc Data Science - 2nd Year - Semester 3',(SELECT id FROM departments WHERE name='B.Sc Data Science'),3),
('B.Sc Data Science - 2nd Year - Semester 4',(SELECT id FROM departments WHERE name='B.Sc Data Science'),4),
('B.Sc Data Science - 3rd Year - Semester 5',(SELECT id FROM departments WHERE name='B.Sc Data Science'),5),
('B.Sc Data Science - 3rd Year - Semester 6',(SELECT id FROM departments WHERE name='B.Sc Data Science'),6),
('M.Sc Data Science - 1st Year - Semester 1',(SELECT id FROM departments WHERE name='M.Sc Data Science'),1),
('M.Sc Data Science - 1st Year - Semester 2',(SELECT id FROM departments WHERE name='M.Sc Data Science'),2),
('M.Sc Data Science - 2nd Year - Semester 3',(SELECT id FROM departments WHERE name='M.Sc Data Science'),3),
('M.Sc Data Science - 2nd Year - Semester 4',(SELECT id FROM departments WHERE name='M.Sc Data Science'),4);
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('teacher','Priya','priya.ds@example.com',NULL,NULL,NULL,'2a59a8b4a55608da717110add1450464','27069c41b3dc388fa408acd3ac6e4183378694e89eab6f3e26abfe66fa14818876d750e7e92d69bd360218e1c5f7502db46a1bf5875e2de27820ce9a52a3d071',TRUE); -- temp password: Teacher@101
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('teacher','Karthika','karthika.ds@example.com',NULL,NULL,NULL,'17ee3ea26756d0ec1462d79729a47f9c','e8dc37502b761ae2b2738e5cb639c1b008ea6dda5ca54986a7e762178d804e368b05a147a8e00f9906bb93637f0e44d743ddaee3b988024e7eb170ddb0aa08d3',TRUE); -- temp password: Teacher@102
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('teacher','Meena','meena.ds@example.com',NULL,NULL,NULL,'93bb420c199c8a3a2d1b2705b568c9e4','342099a130fb61eb1695bb279b0d9f7987d51e6b6c59058a52809f8bc4d374064d7488911e9b0e11b5317ce5721be61b5ec935bcb1d38abaa3fdeb3764147c7e',TRUE); -- temp password: Teacher@103
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('teacher','Nandhini','nandhini.ds@example.com',NULL,NULL,NULL,'08c9f85a6e62156d82e70d1759dedcbc','3dd4af87f00ca4f2206e41569ab8a2032bfad191de7ada2670761ebcb27725b49cc05b97935aba98a7e6d1cc137ef86185c68f84265abdbabe83de9145983ca5',TRUE); -- temp password: Teacher@104
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Divya','divya.ds@example.com',(SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),'BDS001','BDS2026001','698884a1ee1f0453f89e7880d30a7378','5ba8d1c2867549e190e5bba971e0cd79630b9ce955357a5e4cc07311acf5cbbe6f522876b57be76c2e8b0d518183a58125e2a51c1f2b49297ec7ac4d57f268ea',TRUE); -- temp password: Student@101
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Jana','jana.ds@example.com',(SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),'BDS002','BDS2026002','fccff6401598123309ac1850159dad47','016e74fcfeab7a25848df4ee5945afb8537d15ef4752d32aecb360fb931a1facf07f4b76bd56489182e4227d848a29c43d9a56cdcde396d2e45daadfe181b96a',TRUE); -- temp password: Student@102
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Akshaya','akshaya.ds@example.com',(SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),'BDS003','BDS2026003','3f832ecb672f3dee137c1bb430ef6775','be821d2414c7492bcd682ccde165c625dc9e5b965cfff4c94c569c29bbbcc603ebb79d8fd6158937ad1df920284a8ce005544292220fd45c3731be7b56b1fb6d',TRUE); -- temp password: Student@103
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Gopika','gopika.ds@example.com',(SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),'BDS004','BDS2026004','2c9ccb46dfa95fd36d80e0abaa408b77','7c8cda1940f89c6c0ddfc71f79c5fed575d711bb401f982422b700b536d0b1ed9995b7c3ab97d9705989f05c6ac1d6f07e8d2606894c14debe1a3407a057d137',TRUE); -- temp password: Student@104
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Seetha','seetha.ds@example.com',(SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),'BDS005','BDS2026005','14c41931188a51762c4aff4455044aaf','d27cf303ddcda2dbf778f32fbecbddea8de6fdfc32ac7f169521c02c1885b7b2d15465c4e728d3048cbfa0977af4c9f37c2db1be5cbca9420943ab97d3b0e30a',TRUE); -- temp password: Student@105
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Vinothan','vinothan@example.com',(SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),'TEST001','TEST2026001','85e4c6c55227fd535904c765fe5bd335','d5cfbbf49be9a136b811f9bfc287e2b4aa10034551919dafd25cb9de2989b304bac9607f30bc8add71ad256a8ca8d1d3c072c4fcc82d1b752ffd09b6fbcc2877',TRUE); -- temp password: Student@999
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Ananya','ananya.ds@example.com',(SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),'MDS001','MDS2026001','aed6a94c90af77f03dfab3cdcc754e06','b4f86ea41a4417fdab164009a12a1ad4d4400d8001bd41fcfb7f922ff2059a5800a27cb4dab952c858a39d4d6eb95849d1c59ca055f610a3bb31cb9a4cb06280',TRUE); -- temp password: Student@201
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Harini','harini.ds@example.com',(SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),'MDS002','MDS2026002','11dcd7286848cb45eb9e42cfc91e06fe','e239617462315a3668e4e758eb03fc3aebb76ec8fc410ead83dbd51cc21daa0259e43ff4a13dae8ccf8a0047fcc4237e4127dd6ec41af3e48648e6e8d3ebf03f',TRUE); -- temp password: Student@202
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Keerthana','keerthana.ds@example.com',(SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),'MDS003','MDS2026003','f0bdd41e1519b7b029f44ad941f8c516','839241e0b3ed79bc3c0da12af56179db8fab5540d55612b06a41da7e262f785f9ab42650e2b46adffa513ea1ba6990c94c5b1afd63a5d2f78bdbf30ab9305ae9',TRUE); -- temp password: Student@203
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Nivetha','nivetha.ds@example.com',(SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),'MDS004','MDS2026004','11821ca82e1ac7262ad3091a9996d7ff','befdffc4f0919b29e9dd1aa0b41dd8ce3774e82f19e0030e9e3d72e2a30c55e13b90f34088623e456cab204bc2eed48a0549bb6b76bcb5c043b6c3ce5ac5d1b6',TRUE); -- temp password: Student@204
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Pavithra','pavithra.ds@example.com',(SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),'MDS005','MDS2026005','b4635c0810b6bfd419deef37f68a5bb2','7f77281c95db3fc04ac9e22c3bdcd075ffbe1d65ccd1c83c32824270fcdd70caaefb75276009acae2a1d83df1a3e93774531696d72ac09de473e1b41c48bab79',TRUE); -- temp password: Student@205
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Swetha','swetha.ds@example.com',(SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),'MDS006','MDS2026006','67c333c39a3bba8ad5d031e0dfe8e769','a74b5ed5b5bfafea45c90f066f79aa525fbf720027148b256364185cc40333a4e5e91b9b7700de08213e83c2210b62d31a6d85e47f1f20f962d9596c0e2dfb6d',TRUE); -- temp password: Student@206
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Varshini','varshini.ds@example.com',(SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),'MDS007','MDS2026007','35376d24339021e916397333547c820b','cc462ae5c62de2519d1997979b690fd1b98abba16720674f283142499c6358cded98799081c98771cc9197818063401f07c63e820e8f98f27997b4a0a09e5dcb',TRUE); -- temp password: Student@207
INSERT INTO users(role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password) VALUES ('student','Yazhini','yazhini.ds@example.com',(SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),'MDS008','MDS2026008','b9c7de041bac692f8dcfbfa480e9ad32','4b0487131e2598bdb9e5eec0e2f5192501d5ea8f8d3f701be0013ec120ee3c66b5c2388d989fd7a78356002c29ba72936df093df0f93458113192f9fe29669b3',TRUE); -- temp password: Student@208

-- Assign all four teachers to all Data Science semester classes.
INSERT INTO teacher_assignments(teacher_id,class_id)
SELECT u.id,c.id FROM users u CROSS JOIN classes c WHERE u.role='teacher';

-- Two-day demo timetable. 1-hour classes, 11:00-11:15 break, 12:15-13:00 activity/project, 13:00-14:00 lunch.
-- B.Sc 3rd Year Semester 5: Monday
INSERT INTO timetable(class_id,teacher_id,subject,day,period,start_time,end_time) VALUES
((SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),(SELECT id FROM users WHERE email='meena.ds@example.com'),'Machine Learning',1,1,'10:00','11:00'),
((SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),(SELECT id FROM users WHERE email='priya.ds@example.com'),'Python Programming',1,2,'11:15','12:15'),
((SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),(SELECT id FROM users WHERE email='nandhini.ds@example.com'),'Data Visualization',1,3,'14:00','15:00'),
((SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),(SELECT id FROM users WHERE email='karthika.ds@example.com'),'Database Management Systems',1,4,'15:00','16:00'),
-- M.Sc 2nd Year Semester 3: Monday
((SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),(SELECT id FROM users WHERE email='nandhini.ds@example.com'),'Artificial Intelligence',1,1,'10:00','11:00'),
((SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),(SELECT id FROM users WHERE email='karthika.ds@example.com'),'Data Warehousing',1,2,'11:15','12:15'),
((SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),(SELECT id FROM users WHERE email='meena.ds@example.com'),'Machine Learning',1,3,'14:00','15:00'),
((SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),(SELECT id FROM users WHERE email='priya.ds@example.com'),'Advanced Python',1,4,'15:00','16:00'),
-- B.Sc Tuesday
((SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),(SELECT id FROM users WHERE email='karthika.ds@example.com'),'Database Management Systems',2,1,'10:00','11:00'),
((SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),(SELECT id FROM users WHERE email='meena.ds@example.com'),'Machine Learning',2,2,'11:15','12:15'),
((SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),(SELECT id FROM users WHERE email='priya.ds@example.com'),'Python Programming',2,3,'14:00','15:00'),
((SELECT id FROM classes WHERE name='B.Sc Data Science - 3rd Year - Semester 5'),(SELECT id FROM users WHERE email='nandhini.ds@example.com'),'Data Visualization',2,4,'15:00','16:00'),
-- M.Sc Tuesday
((SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),(SELECT id FROM users WHERE email='meena.ds@example.com'),'Machine Learning',2,1,'10:00','11:00'),
((SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),(SELECT id FROM users WHERE email='priya.ds@example.com'),'Advanced Python',2,2,'11:15','12:15'),
((SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),(SELECT id FROM users WHERE email='nandhini.ds@example.com'),'Artificial Intelligence',2,3,'14:00','15:00'),
((SELECT id FROM classes WHERE name='M.Sc Data Science - 2nd Year - Semester 3'),(SELECT id FROM users WHERE email='karthika.ds@example.com'),'Data Warehousing',2,4,'15:00','16:00');

COMMIT;

-- Verification
SELECT role,COUNT(*) FROM users GROUP BY role ORDER BY role;
SELECT d.name AS department,c.name AS class,c.semester FROM classes c JOIN departments d ON d.id=c.dept_id ORDER BY d.name,c.semester;
SELECT day,period,start_time,end_time,subject FROM timetable ORDER BY day,period,subject;
