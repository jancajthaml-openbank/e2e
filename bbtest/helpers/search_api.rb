#require_relative 'rest_service'
#
#require 'net/http'
#require 'uri'
#
#class SearchAPI
  #include RESTServiceHelper
#
  #def graphql(req)
    #uri_base = "http://search_#{$tenant_id}:8080"
    #uri = URI(uri_base)
#
    #client = Net::HTTP.new(uri.host, uri.port)
    #client.read_timeout = 10
    #client.open_timeout = 10
    #client.use_ssl = false
#
    #post(client, "#{uri_base}/graphql", req)
  #end
#
  #def health_check()
#
    #uri_base = "http://search_#{$tenant_id}:8080"
    #uri = URI(uri_base)
#
    #client = Net::HTTP.new(uri.host, uri.port)
    #client.read_timeout = 10
    #client.open_timeout = 10
    #client.use_ssl = false
#
    #get(client, "#{uri_base}/health", req)
  #end
#
#end
