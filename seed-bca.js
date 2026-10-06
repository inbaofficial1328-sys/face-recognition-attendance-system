require('dotenv').config();
const crypto = require('crypto');
const { Pool } = require('pg');

if (!process.env.DATABASE_URL) {
  console.error('DATABASE_URL is missing from .env');
  process.exit(1);
}

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

const hpw = (pw, salt) => crypto.scryptSync(pw, salt, 64).toString('hex');

async function addUser(client, role, name, email, password, extra = {}) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = hpw(password, salt);
  const r = await client.query(`
    INSERT INTO users
      (role,name,email,class_id,college_id,reg_no,salt,password_hash,must_change_password)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,true)
    ON CONFLICT (email) DO UPDATE SET
      name=EXCLUDED.name,
      class_id=EXCLUDED.class_id,
      college_id=EXCLUDED.college_id,
      reg_no=EXCLUDED.reg_no
    RETURNING id
  `, [
    role, name, email.toLowerCase(),
    extra.classId || null, extra.collegeId || null, extra.regNo || null,
    salt, hash
  ]);
  return r.rows[0].id;
}

async function main() {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    let r = await client.query(`
      INSERT INTO departments(name)
      VALUES ('Computer Applications')
      ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name
      RETURNING id
    `);
    const deptId = r.rows[0].id;

    r = await client.query(`
      SELECT id FROM classes
      WHERE name='BCA Final Year' AND dept_id=$1 AND semester=6
      LIMIT 1
    `, [deptId]);

    let classId;
    if (r.rows.length) classId = r.rows[0].id;
    else {
      r = await client.query(`
        INSERT INTO classes(name,dept_id,semester)
        VALUES ('BCA Final Year',$1,6)
        RETURNING id
      `, [deptId]);
      classId = r.rows[0].id;
    }

    const teacherData = [
      ['Dr. Arun Kumar','arun.bca@example.com','Teacher@101'],
      ['Priya Sharma','priya.bca@example.com','Teacher@102'],
      ['Karthik Raj','karthik.bca@example.com','Teacher@103'],
      ['Meena Devi','meena.bca@example.com','Teacher@104'],
      ['Rahul Varun','rahul.bca@example.com','Teacher@105']
    ];

    const teachers = {};
    for (const [name,email,pw] of teacherData) {
      teachers[email] = await addUser(client,'teacher',name,email,pw);
      await client.query(`
        INSERT INTO teacher_assignments(teacher_id,class_id)
        VALUES($1,$2) ON CONFLICT DO NOTHING
      `,[teachers[email],classId]);
    }

    const students = [
      ['Vinothan S','vinothan@example.com','Student@101','BCA001','BCA2026001'],
      ['Arjun Kumar','arjun.bca@example.com','Student@102','BCA002','BCA2026002'],
      ['Divya S','divya.bca@example.com','Student@103','BCA003','BCA2026003'],
      ['Naveen Raj','naveen.bca@example.com','Student@104','BCA004','BCA2026004'],
      ['Harini R','harini.bca@example.com','Student@105','BCA005','BCA2026005'],
      ['Sanjay K','sanjay.bca@example.com','Student@106','BCA006','BCA2026006'],
      ['Keerthana S','keerthana.bca@example.com','Student@107','BCA007','BCA2026007'],
      ['Ajay M','ajay.bca@example.com','Student@108','BCA008','BCA2026008']
    ];

    for (const [name,email,pw,collegeId,regNo] of students) {
      await addUser(client,'student',name,email,pw,{classId,collegeId,regNo});
    }

    // Clean only this class's timetable so rerunning the seed is predictable.
    await client.query('DELETE FROM timetable WHERE class_id=$1',[classId]);

    const timetable = [
      [teachers['arun.bca@example.com'],'Python Programming',1,'09:00','09:50'],
      [teachers['priya.bca@example.com'],'Web Technology',2,'09:50','10:40'],
      [teachers['karthik.bca@example.com'],'Cloud Computing',3,'10:50','11:40'],
      [teachers['meena.bca@example.com'],'Software Engineering',4,'11:40','12:30'],
      [teachers['rahul.bca@example.com'],'Project Development',5,'13:30','14:20']
    ];

    // Monday (day=1). Period 3 is Vinothan's requested face-attendance test period.
    for (const [teacherId,subject,period,start,end] of timetable) {
      await client.query(`
        INSERT INTO timetable(class_id,teacher_id,subject,day,period,start_time,end_time)
        VALUES($1,$2,$3,1,$4,$5,$6)
      `,[classId,teacherId,subject,period,start,end]);
    }

    await client.query('COMMIT');

    console.log('\nFaceTrack BCA Final Year seed completed.\n');
    console.log('Class: BCA Final Year | Semester: 6');
    console.log('Vinothan: vinothan@example.com / Student@101');
    console.log('Period 3 teacher: karthik.bca@example.com / Teacher@103');
    console.log('Period 3: Cloud Computing | 10:50 - 11:40');
    console.log('\nAll seeded users are configured to change their temporary password at first login.');
    console.log('Face descriptors were NOT fabricated. Enroll Vinothan using the real camera from the teacher dashboard.');
  } catch (e) {
    await client.query('ROLLBACK');
    console.error('Seed failed:', e);
    process.exitCode = 1;
  } finally {
    client.release();
    await pool.end();
  }
}

main();
