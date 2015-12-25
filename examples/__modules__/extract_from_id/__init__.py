def extractVariables(variables):
    if variables['id']:
      variables['_tld'] = variables['id'].split('.')[-1]
      variables['_sld'] = variables['id'].split('.')[-2]
      variables['_host'] = variables['id'].split('.')[0]

    return variables