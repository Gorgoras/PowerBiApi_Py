import requests
import json
import powerbiapi_py
import adal
#from powerbiapi_py import global_static as gs

class PowerBI(object):
    def __enter__(self):
        return self

    def __init__(self, user_name, password, client_id):
        self._user_name, self._password, self._client_id = user_name, password, client_id

        self._aad_token = None
        self.is_connected = False
        
        self.PBI_AUTHORITY =  "https://login.microsoftonline.com/common"
        self.PBI_RESOURCE = "https://analysis.windows.net/powerbi/api"

        #API strings
        self.API_BASE = "https://api.powerbi.com/v1.0/myorg/"
        self.API_BASE_GROUP = self.API_BASE + "groups/{wks_id}/"

    def __exit__(self, type, value, traceback):
        pass

    def connect(self):
        try:
            context = adal.AuthenticationContext(
                        self.PBI_AUTHORITY,
                        validate_authority=True,
                        api_version=None)

            token_response = context.acquire_token_with_username_password(
                                    self.PBI_RESOURCE,
                                    self._user_name,
                                    self._password,
                                    self._client_id)

            self._aad_token = token_response["accessToken"]
            self.is_connected = True
        except Exception as ex:
            print(ex.message)

    def _request(self, req,  **params):
        '''
        sends a request to PBI Service. It must be formed beforehand
        '''
        headers = {"Authorization": "Bearer " + self._aad_token}

        log.debug(req)

        response = requests.get(req, headers=headers, **params)
        resp = json.loads(response.text)

        log.debug(response.text)

        if "error" in resp:
            raise RuntimeError("Site returned error: " + str(resp))
        return json.loads(response.text)["value"]

    def get_workspaces(self):
        """
        returns workspaces(groups) as iterator of tuples (id, name)
        """
        groups =  self._request(C.get_api_call("get_groups"))
        ret = []

        #return default workspace (My workspace)
        ret.append( C.Workspace(self))

        for g in groups:
            ret.append( C.Workspace(self, g["id"], g["name"], g["isReadOnly"]))

        return ret

    def get_workspace_by_id(self, workspace_id):
        """get workspace (or group in PBI terminology) by id
        If "default" is specified, then the default workspace is returned
        """
        ret = [w for w in self.get_workspaces() if w.workspace_id == workspace_id]
        return ret[0] if len(ret) > 0 else None

    def get_workspace_by_name(self, workspace_name):
        """
        Returns workspace by name
        """
        ret = [w for w in self.get_workspaces() if w.workspace_name == workspace_name]
        return ret[0] if len(ret) > 0 else None

    def get_report_by_id(self, report_id):
        """Returns report by id"""
        reports  = []
        for w in self.get_workspaces():
            r = w.get_report_by_id(report_id)
            if r: reports.append(r)
        if len(reports) > 1:
            raise ValueError("Duplicate ReportIDs")
        return reports[0] if len(reports) > 0 else None

    def get_report_by_name(self, report_name, workspace_name = None):
        """Retuns powerBI report given name
        If workspace is None, assumes there are no duplicates
        """
        workspace = self.get_workspace_by_name(workspace_name)
        if workspace:
            return workspace.get_report_by_name(report_name)
        else:
            reports  = []
            for w in self.get_workspaces():
                r = w.get_report_by_name(report_name)
                if r: reports.append(r)
            if len(reports) > 1:
                raise ValueError("Duplicate ReportIDs")
            return reports[0] if len(reports) > 0 else None



class Workspace(object):
    def __init__(self, pbi, workspace_id = None, workspace_name = "", isReadOnly = False):
        '''
        initializes the Workspace class. requires powerbi object.
        If workspace id is passed as None(default), it assumes default (My Workspace)
        '''
        self._pbi = pbi
        self.workspace_id = workspace_id
        self.workspace_name = workspace_name
        self.isReadOnly = isReadOnly

    def __str__(self):
        s = "Workspace ID: %s Name: %s" % (self.workspace_id, self.workspace_name) \
                                    if self.workspace_id is not None \
                                    else "Workspace ID: Default Name: My Workspace"
        return s

    def __repr__(self):
        return str(self)

    def get_reports(self):
        return self._get_entities(Report, "get_reports")

    def get_datasets(self):
        return self._get_entities(Dataset, "get_datasets")

    def get_dataset_by_id(self, ds_id):
        ret = [d for d in self.get_datasets() if d.ds_id == ds_id]
        return ret[0] if len(ret) > 0 else None
    
    def _get_entities(self, entity_class, api_call):
        cll = get_api_call(api_call, self.workspace_id)
        ents = self._pbi._request(cll.format(**vars(self)))
        return [entity_class(self, e) for e in ents]


class Report(object):
    def __init__(self, workspace, report):
        self._pbi = workspace._pbi
        self._workspace = workspace
        self.workspace_id = workspace.workspace_id
        self.report_id = report["id"]
        self.report_name = report["name"]
        for key in report:
            setattr(self, key, report[key])
        self.report_dict = report

    def __str__(self):
        return "Report ID: %s Name: %s" % (self.report_id, self.report_name)

    def __repr__(self):
        log.debug(vars(self))
        return "Report ID: %s Name: %s" % (self.report_id, self.report_name)
    def get_token(self,  access_level = "View",  identities = ""):
        return self._get_token("get_report_token", access_level, identities)

    def _get_entities(self, entity_class, api_call):
        cll = get_api_call(api_call, self.workspace_id)
        ents = self._pbi._request(cll.format(**vars(self)))
        return [entity_class(self, e) for e in ents]

    def _get_token(self, api_call,  access_level = "View",  identities = ""):
        cll = get_api_call(api_call, self.workspace_id)
        if identities != "": identities = ', "identities": ' + identities
        headers = {'Authorization': 'Bearer ' + self._pbi._aad_token}
        headers.update( {'Content-type': 'application/json'})

        data = '{{"accessLevel": "{}" {} }} '.format(access_level, identities)
        resp = requests.post(cll.format(**vars(self)), data = data, headers = headers)
        log.debug(resp.text)
        return json.loads(resp.text)["token"]


