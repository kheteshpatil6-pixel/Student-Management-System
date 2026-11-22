import unittest
from app import app
from database import init_db

class StudentManagementSystemTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def login_as_admin(self):
        return self.app.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
            'role': 'admin'
        }, follow_redirects=True)

    def login_as_student(self):
        return self.app.post('/login', data={
            'username': 'MCA-2026-001',
            'password': 'student123',
            'role': 'student'
        }, follow_redirects=True)

    def test_unauthenticated_redirect(self):
        """Unauthenticated user should be redirected to login"""
        response = self.app.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_login_page_renders(self):
        """Login page renders properly with tabs"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Administrator Login', response.data)
        self.assertIn(b'Student / User Login', response.data)

    def test_admin_login_and_dashboard(self):
        """Admin can log in and view dashboard"""
        res = self.login_as_admin()
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Academic Dashboard', res.data)
        self.assertIn(b'admin (admin)', res.data.lower())

    def test_student_login_and_portal(self):
        """Student can log in and view student portal"""
        res = self.login_as_student()
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Student Academic Portal', res.data)
        self.assertIn(b'MCA-2026-001', res.data)

    def test_student_access_control(self):
        """Student cannot access admin-only student directory"""
        self.login_as_student()
        res = self.app.get('/students', follow_redirects=True)
        # Should redirect to student portal with access denied message
        self.assertIn(b'Administrator privileges required', res.data)

    def test_courses_catalog_accessible(self):
        """Both logged in users can view courses catalog"""
        self.login_as_admin()
        res = self.app.get('/courses')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Courses Catalog', res.data)

    def test_api_stats(self):
        """Public or system API returns stats"""
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total_students', data)
        self.assertIn('total_courses', data)

    def test_logout(self):
        """Logout clears session and returns to login"""
        self.login_as_admin()
        res = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Sign In to Portal', res.data)

if __name__ == '__main__':
    unittest.main()
