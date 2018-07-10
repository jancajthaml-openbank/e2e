require 'json'
require_relative '../shims/deep_diff'

step "I call :http_method :url" do |http_method, url, body = nil|
  @resp = HttpClient.any.call(http_method, url, body)
end

step "response status should be :http_status" do |http_status|
  expect(@resp.code.to_i).to eq(http_status)
end

step "response content should be:" do |content|
  expected_body = JSON.parse(content)

  begin
    resp_body = JSON.parse(@resp.body)
    resp_body.deep_diff(expected_body).each do |key, array|
      (have, want) = array
      raise "unexpected attribute \"#{key}\" in response \"#{@resp.body}\" expected \"#{expected_body.to_json}\"" if want.nil?
      raise "\"#{key}\" expected \"#{want}\" but got \"#{have}\" instead"
    end
  rescue JSON::ParserError
    raise "invalid response got \"#{@resp.body.strip}\", expected \"#{expected_body.to_json}\""
  end
end

