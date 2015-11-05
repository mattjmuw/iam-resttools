# IRWS service interface
#

import os
import string
import time
import re
import random
import copy
from urllib import quote_plus

import json

from resttools.dao import IRWS_DAO
from resttools.models.irws import UWNetId
from resttools.models.irws import Regid
from resttools.models.irws import Subscription
from resttools.models.irws import Person
from resttools.models.irws import Profile
from resttools.models.irws import UWhrPerson
from resttools.models.irws import SdbPerson
from resttools.models.irws import CascadiaPerson
from resttools.models.irws import SccaPerson
from resttools.models.irws import SupplementalPerson
from resttools.models.irws import Pac
from resttools.models.irws import Name
from resttools.models.irws import QnA
from resttools.models.irws import GenericPerson

from resttools.exceptions import DataFailureException

import logging
logger = logging.getLogger(__name__)


class IRWS(object):

    def __init__(self, conf):

        self._service_name = conf['SERVICE_NAME']
        self._conf = conf
        self.new_ids = set([])

    def _get_code_from_error(self, message):
        try:
            code = int(json.loads(message)['error']['code'])
        except:
            code = (-1)
        return code

    # v2 - no change
    def get_uwnetid(self, eid=None, regid=None, netid=None, source=None, status=None, ret_array=False):
        """
        Returns an irws.UWNetid object for the given netid or regid.  If the
        netid isn't found, nothing will be returned.  If there is an error
        communicating with the IRWS, a DataFailureException will be thrown.
        if 'all' an array is returned with all the matching netids.
        """

        status_str = ''
        if status is not None:
            status_str = '&status=%d' % status
        dao = IRWS_DAO(self._conf)
        if eid is not None and source is not None:
            url = "/%s/v2/uwnetid?validid=%d=%s%s" % (self._service_name, source, eid, status_str)
        elif regid is not None:
            url = "/%s/v2/uwnetid?validid=regid=%s%s" % (self._service_name, regid, status_str)
        elif netid is not None:
            url = "/%s/v2/uwnetid?validid=uwnetid=%s%s" % (self._service_name, netid, status_str)
        else:
            return None
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        id_data = json.loads(response.data)['uwnetid']
        if ret_array:
            ret = []
            for n in range(0, len(id_data)):
                ret.append(self._uwnetid_from_json_obj(id_data[n]))
            return ret
        else:
            return self._uwnetid_from_json_obj(id_data[0])

    # v2 - no change
    def get_person(self, netid=None, regid=None, eid=None):
        """
        Returns an irws.Person object for the given netid or regid.  If the
        netid isn't found, nothing will be returned.  If there is an error
        communicating with the IRWS, a DataFailureException will be thrown.
        """
        dao = IRWS_DAO(self._conf)
        url = None
        if netid is not None:
            url = "/%s/v2/person?uwnetid=%s" % (self._service_name, netid.lower())
        elif regid is not None:
            url = "/%s/v2/person?validid=regid=%s" % (self._service_name, regid)
        elif eid is not None:
            url = "/%s/v2/person?validid=1=%s" % (self._service_name, eid)
        else:
            return None
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._person_from_json(response.data)

    # v2 - no change
    def get_regid(self, netid=None, regid=None):
        """
        Returns an irws.Regid object for the given netid or regid.  If the
        netid isn't found, nothing will be returned.  If there is an error
        communicating with the IRWS, a DataFailureException will be thrown.
        """
        dao = IRWS_DAO(self._conf)
        url = None
        if netid is not None:
            url = "/%s/v2/regid?uwnetid=%s" % (self._service_name, netid.lower())
        elif regid is not None:
            url = "/%s/v2/regid?validid=regid=%s" % (self._service_name, regid)
        else:
            return None
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._regid_from_json(response.data)

    # v2 - changes
    def get_pw_recover_info(self, netid):
        """
        Returns an irws.Profile object containing password recovery fields
        for the given netid or regid.  If the
        netid isn't found, nothing will be returned.  If there is an error
        communicating with the IRWS, a DataFailureException will be thrown.
        """
        dao = IRWS_DAO(self._conf)
        url = "/%s/v2/profile/validid=uwnetid=%s" % \
            (self._service_name, netid.lower())
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._pw_recover_from_json(response.data)

    def put_pw_recover_info(self, netid, profile):
        """
        Updates recover info in netid's profile
        """
        dao = IRWS_DAO(self._conf)
        url = "/%s/v2/profile/validid=uwnetid=%s" % (self._service_name, netid)
        response = dao.putURL(url, {"Content-type": "application/json"}, json.dumps(profile.json_data()))

        if response.status >= 500:
            raise DataFailureException(url, response.status, response.data)

        return response.status

    def get_name_by_netid(self, netid):
        """
        Returns a resttools.irws.Name object for the given netid.  If the
        netid isn't found, nothing will be returned.  If there is an error
        communicating with the IRWS, a DataFailureException will be thrown.
        """

        dao = IRWS_DAO(self._conf)
        url = "/%s/v2/name/uwnetid=%s" % (self._service_name, netid.lower())
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._name_from_json(response.data)

    def get_uwhr_person(self, eid, source='uwhr'):
        """
        Returns an irws.UWhrPerson object for the given eid.
        If the person is not an employee, returns None.
        If the netid isn't found, throws IRWSNotFound.
        If there is an error contacting IRWS, throws DataFailureException.
        """
        dao = IRWS_DAO(self._conf)

        url = "/%s/v2/person/%s/%s" % (self._service_name, source, eid)
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._uwhr_person_from_json(response.data)

    def get_sdb_person(self, vid):
        """
        Returns an irws.SdbPerson object for the given eid.
        If the person is not a student, returns None.
        If the netid isn't found, throws IRWSNotFound.
        If there is an error contacting IRWS, throws DataFailureException.
        """
        dao = IRWS_DAO(self._conf)

        url = "/%s/v2/person/sdb/%s" % (self._service_name, vid)
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._sdb_person_from_json(response.data)

    def get_cascadia_person(self, id):
        """
        Returns an irws.CascadiaPerson object for the given id.
        If the netid isn't found, throws IRWSNotFound.
        If there is an error contacting IRWS, throws DataFailureException.
        """
        dao = IRWS_DAO(self._conf)

        url = "/%s/v2/person/cascadia/%s" % (self._service_name, id)
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._cascadia_person_from_json(response.data)

    def get_scca_person(self, id):
        """
        Returns an irws.SccaPerson object for the given id.
        If the netid isn't found, throws IRWSNotFound.
        If there is an error contacting IRWS, throws DataFailureException.
        """
        dao = IRWS_DAO(self._conf)

        url = "/%s/v2/person/scca/%s" % (self._service_name, id)
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._scca_person_from_json(response.data)

    def get_supplemental_person(self, id):
        """
        Returns an irws.SupplementalPerson object for the given id.
        If the netid isn't found, throws IRWSNotFound.
        If there is an error contacting IRWS, throws DataFailureException.
        """
        dao = IRWS_DAO(self._conf)

        url = "/%s/v2/person/supplemental/%s" % (self._service_name, id)
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._supplemental_person_from_json(response.data)

    def get_generic_person(self, uri):
        """
        Returns an irws.GenericPerson object for the given uri.
        The uris come in from values in irws.Person.identifiers.
        Raises DataFailureExeption on error.
        """
        dao = IRWS_DAO(self._conf)

        url = '/%s/v2%s' % (self._service_name, uri)
        response = dao.getURL(url, {'Accept': 'application/json'})

        if response.status == 404:
            return None
        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._generic_person_from_json(response.data)

    def get_subscription(self, netid, subscription):
        """
        Returns an irws.Subscription object for the given netid.  If the
        netid isn't found, nothing will be returned.  If there is an error
        communicating with the IRWS, a DataFailureException will be thrown.
        """
        dao = IRWS_DAO(self._conf)
        url = "/%s/v2/subscription?uwnetid=%s&subscription=%d" % (self._service_name, netid.lower(), subscription)
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._subscription_from_json(response.data)

    def put_pac(self, eid, source='uwhr'):
        """
        Creates a PAC for the employee.  Returns the Pac.
        """
        dao = IRWS_DAO(self._conf)
        url = "/%s/v2/person/%s/%s/pac" % (self._service_name, source, eid)
        response = dao.putURL(url, {"Accept": "application/json"}, '')

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._pac_from_json(response.data)

    def verify_sdb_pac(self, sid, pac):
        """
        Verifies a permanent student PAC. Returns 200 (ok) or 400 (no)
        """
        dao = IRWS_DAO(self._conf)
        url = "/%s/v2/person/sdb/%s?pac=%s" % (self._service_name,
                                               quote_plus(sid), quote_plus(pac))
        response = dao.getURL(url, {"Accept": "application/json"})

        if (response.status == 200 or response.status == 400 or response.status == 404):
            return response.status
        raise DataFailureException(url, response.status, response.data)

    def verify_sc_pin(self, netid, pin):
        """
        Verifies a service center one-time pin. Returns 200 (ok) or 400 (no).
        OK clears the pin.
        """
        dao = IRWS_DAO(self._conf)

        # make sure there is a pin subscription
        url = "/%s/v2/subscription/63/%s" % (self._service_name, netid)
        response = dao.getURL(url, {"Accept": "application/json"})
        if response.status == 200:
            sub = json.loads(response.data)['subscription'][0]
            # verify pending subscription and unexpired, unused pac
            if sub['status_code'] != '23' or sub['pac'] != 'Y':
                return 404
        else:
            return response.status

        url = "/%s/v2/subscribe/63/%s?action=1&pac=%s" % (self._service_name, netid, pin)
        response = dao.getURL(url, {"Accept": "application/json"})
        if response.status == 200:
            # TODO: The following series of deletes don't appear to work in a Live setting
            # delete the pac
            url = "/%s/v2/subscription/63/%s/pac" % (self._service_name, netid)
            response = dao.deleteURL(url, {"Accept": "application/json"})
            if response.status != 200:
                # the pin was good.  we return OK, but note the error
                logging.warn('Delete SC pin failed: %d' % response.status)
            # delete the subscription
            url = "/%s/v2/subscription/63/%s" % (self._service_name, netid)
            response = dao.deleteURL(url, {"Accept": "application/json"})
            if response.status != 200:
                logging.warn('Delete SC subscription failed: %d' % response.status)
            return 200

        if (response.status == 400 or response.status == 404):
            return response.status
        raise DataFailureException(url, response.status, response.data)

    def get_qna(self, netid):
        """
        Returns a list irws.QnA for the given netid.
        """
        dao = IRWS_DAO(self._conf)

        url = "/%s/v2/qna?uwnetid=%s" % (self._service_name, netid)
        response = dao.getURL(url, {"Accept": "application/json"})

        if response.status == 404:
            return None

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        return self._qna_from_json(response.data)

    def get_verify_qna(self, netid, answers):
        """
        Verifies that all answers are present and that all are correct.
        answers: dict ('ordinal': 'answer')
        """
        dao = IRWS_DAO(self._conf)
        q_list = self.get_qna(netid)
        for q in q_list:
            if q.ordinal not in answers:
                logging.debug('q %s, no answer' % q.ordinal)
                return False
            ans = re.sub(r'\W+', '', answers[q.ordinal])
            url = "/%s/v2/qna/%s/%s/check?ans=%s" % (self._service_name, q.ordinal, netid, ans)
            response = dao.getURL(url, {"Accept": "application/json"})
            if response.status == 404:
                logging.debug('q %s, wrong answer' % q.ordinal)
                return False
            if response.status != 200:
                logging.debug('q %s, error return: %d' % (q.ordinal, response.status))
                return False
            logging.debug('q %s, correct answer' % q.ordinal)
        return True

    def verify_person_attribute(self, netid, attribute, value):
        """
        Verify that the given attribute (eg birthdate) matches the value for the netid.

        Rather than chase all of the person identifier urls client-side, irws will return the
        list of identifiers. For birthdate, IRWS has the added value of discarding silly
        birthdates and matching on partial birthdates.
        """
        dao = IRWS_DAO(self._conf)
        url = "/%s/v2/person?uwnetid=%s&%s=%s" % (self._service_name, quote_plus(netid),
                                                  quote_plus(attribute), quote_plus(value))
        return dao.getURL(url, {'Accept': 'application/json'}).status == 200

    def _uwhr_person_from_json(self, data):
        """
        Internal method, for creating the UWhrPerson object.
        """
        person_data = json.loads(data)['person'][0]
        person = UWhrPerson()
        person.validid = person_data['validid']
        person.regid = person_data['regid']
        if 'studentid' in person_data:
            person.studentid = person_data['studentid']
        if 'birthdate' in person_data:
            person.birthdate = person_data['birthdate']

        if 'fname' in person_data:
            person.fname = person_data['fname']
        if 'lname' in person_data:
            person.lname = person_data['lname']

        if 'emp_ecs_code' in person_data:
            person.emp_ecs_code = person_data['emp_ecs_code']
        if 'emp_status_code' in person_data:
            person.emp_status_code = person_data['emp_status_code']
        person.source_code = person_data['source_code']
        person.source_name = person_data['source_name']
        person.status_code = person_data['status_code']
        person.status_name = person_data['status_name']
        if 'contact_email' in person_data:
            person.contact_email = person_data['contact_email']
        if 'workday_home_email' in person_data:
            person.workday_home_email = person_data['workday_home_email']
        if 'org_supervisor' in person_data:
            person.org_supervisor = person_data['org_supervisor']

        if 'pac' in person_data:
            person.pac = person_data['pac']
        if 'in_feed' in person_data:
            person.in_feed = person_data['in_feed']

        if 'wp_publish' in person_data:
            person.wp_publish = person_data['wp_publish']
        else:
            person.wp_publish = 'Y'
        return person

    def _sdb_person_from_json(self, data):
        """
        Internal method, for creating the SdbPerson object.
        """
        person_data = json.loads(data)['person'][0]
        person = SdbPerson()
        person.validid = person_data['validid']
        person.regid = person_data['regid']
        person.studentid = person_data['studentid']
        if 'birthdate' in person_data:
            person.birthdate = person_data['birthdate']

        person.fname = person_data['fname']
        person.lname = person_data['lname']

        person.categories = person_data['categories']
        person.source_code = person_data['source_code']
        person.source_name = person_data['source_name']
        person.status_code = person_data['status_code']
        person.status_name = person_data['status_name']

        if 'pac' in person_data:
            person.pac = person_data['pac']
        if 'in_feed' in person_data:
            person.in_feed = person_data['in_feed']
        if 'cnet_id' in person_data:
            person.cnet_id = person_data['cnet_id']
        if 'cnet_user' in person_data:
            person.cnet_user = person_data['cnet_user']

        if 'wp_publish' in person_data:
            person.wp_publish = person_data['wp_publish']
        else:
            person.wp_publish = 'Y'
        return person

    def _cascadia_person_from_json(self, data):
        """
        Internal method, for creating the CascadiaPerson object.
        """
        person_data = json.loads(data)['person'][0]
        person = CascadiaPerson()
        person.validid = person_data['validid']
        person.regid = person_data['regid']
        person.lname = person_data['lname']
        person.categories = person_data['categories']
        if 'birthdate' in person_data:
            person.birthdate = person_data['birthdate']
        if 'department' in person_data:
            person.department = person_data['department']
        if 'in_feed' in person_data:
            person.in_feed = person_data['in_feed']
        return person

    def _scca_person_from_json(self, data):
        """
        Internal method, for creating the SccaPerson object.
        """
        person_data = json.loads(data)['person'][0]
        person = SccaPerson()
        person.validid = person_data['validid']
        person.regid = person_data['regid']
        person.lname = person_data['lname']
        person.categories = person_data['categories']
        if 'birthdate' in person_data:
            person.birthdate = person_data['birthdate']
        if 'scca_company' in person_data:
            person.scca_company = person_data['scca_company']
        if 'scca_cca_eppn' in person_data:
            person.scca_cca_eppn = person_data['scca_cca_eppn']
        if 'scca_fhc_eppn' in person_data:
            person.scca_fhc_eppn = person_data['scca_fhc_eppn']
        if 'in_feed' in person_data:
            person.in_feed = person_data['in_feed']
        return person

    def _supplemental_person_from_json(self, data):
        """
        Internal method, for creating the SupplementalPerson object.
        """
        person_data = json.loads(data)['person'][0]
        person = SupplementalPerson()
        person.validid = person_data['validid']
        person.regid = person_data['regid']
        person.lname = person_data['lname']

        person.categories = person_data['categories']
        person.source_code = person_data['source_code']
        person.source_name = person_data['source_name']
        person.status_code = person_data['status_code']
        person.status_name = person_data['status_name']
        if 'comment_code' in person_data:
            person.comment_code = person_data['comment_code']
        if 'comment_name' in person_data:
            person.comment_name = person_data['comment_name']
        if 'college' in person_data:
            person.college = person_data['college']

        if 'in_feed' in person_data:
            person.in_feed = person_data['in_feed']

        person.id_proofing = person_data.get('id_proofing', {})
        person.contact_email = person_data.get('contact_email', [])

        return person

    def _person_from_json(self, data):
        persj = json.loads(data)['person'][0]
        idj = persj['identity']
        person = Person()
        person.regid = idj['regid']
        person.lname = idj['lname']
        person.fname = idj['fname']
        person.identifiers = copy.deepcopy(idj['identifiers'])
        return person

    def _regid_from_json(self, data):
        rj = json.loads(data)['regid'][0]
        regid = Regid()
        regid.regid = rj['regid']
        regid.entity_code = rj['entity_code']
        regid.entity_name = rj['entity_name']
        regid.status_code = rj['status_code']
        regid.status_name = rj['status_name']
        return regid

    def _pw_recover_from_json(self, data):
        info = json.loads(data)['profile'][0]
        ret = Profile()
        if 'validid' in info:
            ret.validid = info['validid']
        if 'recover_contacts' in info:
            ret.recover_contacts = info['recover_contacts']
        if 'recover_block_reasons' in info:
            ret.recover_block_reasons = info['recover_block_reasons']
        return ret

    def _uwnetid_from_json_obj(self, id_data):
        uwnetid = UWNetId()
        uwnetid.uwnetid = id_data['uwnetid']
        uwnetid.validid = id_data['validid']
        uwnetid.uid = id_data['uid']
        return uwnetid

    def _subscription_from_json(self, data):
        sub_data = json.loads(data)['subscription'][0]
        subscription = Subscription()
        subscription.uwnetid = sub_data['uwnetid']
        subscription.subscription_code = sub_data['subscription_code']
        subscription.subscription_name = sub_data['subscription_name']
        return subscription

    def _pac_from_json(self, data):
        pac_data = json.loads(data)['person'][0]
        pac = Pac()
        pac.pac = pac_data['pac']
        pac.expiration = pac_data['expiration']
        return pac

    def _name_from_json(self, data):
        nd = json.loads(data)['name'][0]
        name = Name()
        name.validid = nd['validid']
        if 'formal_cname' in nd:
            name.formal_cname = nd['formal_cname']
        if 'formal_fname' in nd:
            name.formal_fname = nd['formal_fname']
        if 'formal_sname' in nd:
            name.formal_lname = nd['formal_sname']
        if 'formal_privacy' in nd:
            name.formal_privacy = nd['formal_privacy']
        if 'display_cname' in nd:
            name.display_cname = nd['display_cname']
        if 'display_fname' in nd:
            name.display_fname = nd['display_fname']
        if 'display_mname' in nd:
            name.display_mname = nd['display_mname']
        if 'display_sname' in nd:
            name.display_lname = nd['display_sname']
        if 'display_privacy' in nd:
            name.display_privacy = nd['display_privacy']
        return name

    def _qna_from_json(self, data):
        q_list = json.loads(data)['qna']
        ret = []
        for q in q_list:
            qna = QnA()
            qna.uwnetid = q['uwnetid']
            qna.ordinal = q['ordinal']
            qna.question = q['question']
            # qna.answer = q['answer']
            ret.append(qna)
        return ret

    def _generic_person_from_json(self, data):
        """
        Internal method to create a GenericPerson object.
        """
        person_data = json.loads(data)['person'][0]
        person = GenericPerson()
        attributes = [attribute for attribute in dir(GenericPerson) if not attribute.startswith('_')]
        for attribute in attributes:
            # set the attribute to the value in person_data, or if not set there,
            # the default attribute value
            setattr(person, attribute, person_data.get(attribute, getattr(GenericPerson, attribute)))
        return person
