require_relative 'rest_service'

class LakeAPI
  include RESTServiceHelper

  def health_check()
    get("http://lake:9999/health")
  end

end
