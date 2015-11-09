#!/usr/bin/env python3.5
import unittest
from unittest import mock
import tempfile
import os
from ncsales import cli


class TestCli(unittest.TestCase):

    def test_get_data(self):
        with tempfile.NamedTemporaryFile() as source:
            source.write(b'1, web, 34.33\n')
            source.seek(0)
            self.assertEqual([['1', 'web', '34.33']],
                             list(cli.get_data(source.name)))

    def test_get_data_from_empty_file(self):
        with tempfile.NamedTemporaryFile() as source:
            source.write(b'')
            source.seek(0)
            self.assertEqual([], list(cli.get_data(source.name)))

    def test_parse_row(self):
        row = ['1', 'web', '23.45']
        self.assertEqual([1, 'web', 23.45], cli.parse_row(row))

        with self.assertRaises(cli.ValidationError) as error:
            cli.parse_row([])
        self.assertEquals(str(error.exception), 'Malformed row')

        with self.assertRaises(cli.ValidationError) as error:
            cli.parse_row(['qw', 'web', '23.45'])
        self.assertEquals(str(error.exception), 'Bad contact id')

        with self.assertRaises(cli.ValidationError) as error:
            cli.parse_row(['1', 'people', '23.45'])
        self.assertEquals(str(error.exception), 'Unknown event type')

        with self.assertRaises(cli.ValidationError) as error:
            cli.parse_row(['1', 'web', ''])
        self.assertEquals(str(error.exception), 'Bad score')

    def test_get_quartile_label(self):
        self.assertEquals('platinum', cli.get_quartile_label(80))
        self.assertEquals('gold', cli.get_quartile_label(60))
        self.assertEquals('silver', cli.get_quartile_label(40))
        self.assertEquals('bronze', cli.get_quartile_label(20))
        self.assertEquals('', cli.get_quartile_label(120))

    def test_process_file(self):
        the_file = os.path.abspath(__file__)
        with mock.patch('ncsales.cli.get_data') as mock_get_data:
            mock_get_data.return_value = [['1', 'web', '34.33'],
                                          ['', 'webinar', '55.4'],
                                          ['3', 'webinar', '15.4'],
                                          ['2', 'webinar', '55.4']]
            self.assertEqual(
                [(1, 'bronze', 4),
                 (2, 'platinum', 100),
                 (3, 'bronze', 0)], list(cli.process_file(the_file))
            )

    def test_process_file_with_one_row(self):
        the_file = os.path.abspath(__file__)
        with mock.patch('ncsales.cli.get_data') as mock_get_data:
            mock_get_data.return_value = [['1', 'web', '34.33']]
            self.assertEqual(
                [(1, 'bronze', 0)], list(cli.process_file(the_file))
            )

    def test_process_file_with_eqauls_scores(self):
        the_file = os.path.abspath(__file__)
        with mock.patch('ncsales.cli.get_data') as mock_get_data:
            mock_get_data.return_value = [['1', 'web', '34.33'],
                                          ['2', 'web', '34.33']]
            self.assertEqual(
                [(1, 'bronze', 0), (2, 'bronze', 0)],
                list(cli.process_file(the_file))
            )

    def test_integration(self):
        with tempfile.NamedTemporaryFile() as source:
            source.write(b'''\
1, web, 34.33
1, email, 3.4
1, social, 4
2, webinar, 55.4
2, social, 15
3, social, 25
3, email, 63
''')
            source.seek(0)
            self.assertEqual(
                [(1, 'bronze', 0), (2, 'platinum', 100), (3, 'platinum', 77)],
                list(cli.process_file(source.name))
            )
