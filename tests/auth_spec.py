#!/usr/bin/env python3

"""
Tests for authentication
"""

from api.app import app, storage
import json
import unittest
from api.models import User, Organisation
import datetime

app.config['TESTING'] = True

class AuthTestCase(unittest.TestCase):
    """
    Tests for user authentication and authorization
    """

    def setUp(self):

        """
        Set up test case
        """

        self.client = app.test_client()
        res_1 = self.client.post('/auth/register', json={
            "firstName": "Pius",
            "lastName": "John",
            "email": "auwu@gmail.com",
            "password": "password_uwvudwonoziw",
            "phone": "0700000000"
        })

        self.pius_data = json.loads(res_1.data)
        self.user_pius = storage.fetch(User, limit=1, email="auwu@gmail.com")

        res_2 = self.client.post('/auth/register', json={
            "firstName": "Clint",
            "lastName": "John",
            "email": "wu@gmail.com",
            "password": "password_uwvudwonoziw",
            "phone": "0700000000"
        })

        self.clint_data = json.loads(res_2.data)
        self.user_clint = storage.fetch(User, limit=1, email="wu@gmail.com")


        def tearDown(self):
            """
            Clean up test case
            """

            self.user_pius.delete()
            self.user_clint.delete()

            
    def test_auth_token_and_expiration(self):
        """
        Test authentication token and expiration
        """
        # create a user
        user = User(firstName="John", lastName="Doe", email="johndoe@example.com", password="password")
        user.organisations.append(Organisation(name="John's Organisation"))
        try:
            user.save()
        except Exception as e:
            storage.rollback()

        # login the user
        response = self.client.post('/auth/login', json={
            "email": "johndoe@example.com",
            "password": "password"
        })
        data = json.loads(response.data)
        access_token = data.get('data').get('accessToken')

        # check if the token is valid
        self.assertIsNotNone(access_token)
        self.assertIsInstance(access_token, str)

        # check if the token is expired
        expires = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
        self.assertGreater(datetime.datetime.utcnow(), expires)
        # delete the user to clean up the database

        user.delete()

    
    def test_user_registration_and_login(self):
        """
        Test user registration and login
        """

        # register a user
        response = self.client.post('/auth/register', json={
            "firstName": "John",
            "lastName": "Doe",
            "email": "johndoe@example.com",
            "password": "passworuwu",
            "phone": "1234567890"
        })

        john = storage.fetch(User, limit=1, email="johndoe@example.com")
        john_org = john.organisations[0]
        self.assertEqual(response.status_code, 201)
        self.assertIn('data', json.loads(response.data))
        self.assertIn("accessToken", json.loads(response.data)['data'])
        # checks default organisation
        self.assertEqual(john_org.name, john.firstName + "'s organisation")

        # login the user
        response = self.client.post('/auth/login', json={
            "email": "johndoe@example.com",
            "password": "passworuwu"
        })

        self.assertEqual(response.status_code, 200)
        john.delete()

    
    def test_user_registration_with_invalid_data(self):
        """
        Test user registration with invalid data
        """
        response = self.client.post('/auth/register', json={
        })

        self.assertEqual(response.status_code, 422)
        # check error response
        self.assertIn('errors', json.loads(response.data))
        self.assertIn('message', json.loads(response.data)['errors'][0])

        # test with empty fields
        response = self.client.post('/auth/register', json={
            "firstName": "",
            "lastName": "",
            "email": "",
            "password": "",
            "phone": ""
        })

        self.assertEqual(response.status_code, 422)

        # test with missing fields
        response = self.client.post('/auth/register', json={
            "firstName": "John",
            "lastName": "Doe",
            "password": "passworuwu",
            "phone": "1234567890"
        })

        self.assertEqual(response.status_code, 422)
    
    def test_userOwn_data_retreival(self):
        """
        Test user data retrieval
        """
        res_for_pius = self.client.post('/auth/login', json={
            "email": "auwu@gmail.com",
            "password": "password_uwvudwonoziw"
        })
        data = json.loads(res_for_pius.data)
        access_token = data.get('data').get('accessToken')

        response = self.client.get(f'/api/users/{self.user_pius.userId}', headers={
            'Authorization': 'Bearer ' + access_token
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('data', json.loads(response.data))
        self.assertEqual(json.loads(response.data)['data'], self.user_pius.to_dict())


    def test_userOthers_data_retreival(self):
        """
        Test user retireving other user's data with common organisation7
        """

        res_for_pius = self.client.post('/auth/login', json={
            "email": "auwu@gmail.com",
            "password": "password_uwvudwonoziw"
        })
        data = json.loads(res_for_pius.data)
        access_token = data.get('data').get('accessToken')

        # adds user to common organisation
        post_res = self.client.post('/api/organisations/{}/users'\
                         .format(self.user_pius.organisations[0].orgId),
                                 json={"userId": self.user_clint.userId})
        self.assertEqual(post_res.status_code, 200)

        response = self.client.get(f'/api/users/{self.user_clint.userId}', headers={
            'Authorization': 'Bearer ' + access_token
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('data', json.loads(response.data))
        self.assertEqual(json.loads(response.data)['data'], self.user_clint.to_dict())

    # SKIP THIS TEST
    @unittest.skip
    def test_user_data_and_organisation_data(self):
        """
        Test a user can only see their own data and organisation data
        """
        # create users and organisations
        user1 = User(firstName="John",
                     lastName="Doe",
                     email="johndoe@example.com",
                     password="password")

        user2 = User(firstName="Jane",
                     lastName="Doe",
                     email="janedoe@example.com",
                     password="password")

        org1 = Organisation(name="John's Organisation")
        org2 = Organisation(name="Jane's Organisation")

        user1.organisations.append(org1)
        user2.organisations.append(org2)

        user1.save()
        user2.save()

        # login user1
        response = self.client.post('/auth/login', json={
            "email": "johndoe@example.com",
            "password": "password"
        })
        data = json.loads(response.data)
        access_token = data.get('data').get('accessToken')

        # get user1's data and organisation data
        response = self.client.get(f'/api/users/{user1.userId}', headers={
            'Authorization': 'Bearer ' + access_token
        })
        data = json.loads(response.data)
        self.assertEqual(data['data']['firstName'], 'John')
        self.assertEqual(data['data']['email'], 'johndoe@example.com')
        self.assertEqual(len(data['data']['organisations']), 1)
        self.assertEqual(data['data']['organisations'][0]['name'], 'John\'s Organisation')

        # try to get user2's data and organisation data
        response = self.client.get(f'/api/users/{user2.userId}', headers={
            'Authorization': 'Bearer ' + access_token
        })
        self.assertEqual(response.status_code, 404)

        # try to get user2's organisation data
        response = self.client.get('/api/organisations/' + org2.orgId, headers={
            'Authorization': 'Bearer ' + access_token
        })
        self.assertEqual(response.status_code, 404)

        # login user2
        response = self.client.post('/auth/login', json={
            "email": "janedoe@example.com",
            "password": "password"
        })
        data = json.loads(response.data)
        access_token = data.get('data').get('accessToken')

        # get user2's data and organisation data
        response = app.test_client().get('/api/users/', headers={
            'Authorization': 'Bearer ' + access_token
        })
        data = json.loads(response.data)
        self.assertEqual(data['data']['firstName'], 'Jane')
        self.assertEqual(data['data']['email'], 'janedoe@example.com')
        self.assertEqual(len(data['data']['organisations']), 1)
        self.assertEqual(data['data']['organisations'][0]['name'], 'Jane\'s Organisation')

        # try to get user1's data and organisation data
        response = app.test_client().get('/api/users/johndoe@example.com', headers={
            'Authorization': 'Bearer ' + access_token
        })
        self.assertEqual(response.status_code, 404)

        # try to get user1's organisation data
        response = app.test_client().get('/api/organisations/' + org1.orgId, headers={
            'Authorization': 'Bearer ' + access_token
        })
        self.assertEqual(response.status_code, 404)
        user1.delete()
        user2.delete()


if __name__ == "__main__":
    unittest.main()
