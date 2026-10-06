require('dotenv').config();

const crypto = require('crypto');
const { Pool } = require('pg');

const [, , emailArg, passwordArg] = process.argv;

if (!emailArg || !passwordArg) {
  console.log('Usage: node resetpw.js <email> <newTempPassword>');
  process.exit(1);
}

if (!process.env.DATABASE_URL) {
  console.error('DATABASE_URL is missing from .env');
  process.exit(1);
}

const email = emailArg.trim().toLowerCase();
const password = passwordArg;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

async function resetPassword() {
  try {
    const check = await pool.query(
      `SELECT id, name, email, role
       FROM users
       WHERE LOWER(email) = $1`,
      [email]
    );

    if (!check.rows.length) {
      console.log(`No Neon user found with email: ${email}`);
      process.exitCode = 1;
      return;
    }

    const salt = crypto.randomBytes(16).toString('hex');

    const passwordHash = crypto
      .scryptSync(password, salt, 64)
      .toString('hex');

    await pool.query(
      `UPDATE users
       SET salt = $1,
           password_hash = $2,
           must_change_password = TRUE
       WHERE LOWER(email) = $3`,
      [salt, passwordHash, email]
    );

    const user = check.rows[0];

    console.log('');
    console.log('NEON PASSWORD RESET SUCCESSFUL');
    console.log('Name :', user.name);
    console.log('Email:', user.email);
    console.log('Role :', user.role);
    console.log('');
    console.log('Password updated directly in Neon PostgreSQL.');
    console.log('The user must change the temporary password after login.');
  } catch (err) {
    console.error('Password reset failed:', err.message);
    process.exitCode = 1;
  } finally {
    await pool.end();
  }
}

resetPassword();