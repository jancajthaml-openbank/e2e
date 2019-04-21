require 'json'
require 'json-diff'
require 'deepsort'

step "I request search" do |req|
  url = "http://127.0.0.1:8080/graphql"
  body = "{\"query\":\"" + req.inspect[1..-2] + "\",\"variables\":null,\"operationName\":null}"

  HTTPHelper.prepare_request({
    :method => "POST",
    :url => url,
    :body => body
  })
end

step "search responds with :http_status" do |http_status, body = nil|
  eventually(timeout: 30, backoff: 2) {
    HTTPHelper.perform_request()
    http_status = [http_status] unless http_status.kind_of?(Array)
    expect(http_status).to include(HTTPHelper.response[:code])
  }

  return if body.nil?

  expectation = JSON.parse(body)
  expectation.deep_sort!

  begin
    resp_body = JSON.parse(HTTPHelper.response[:body])
    resp_body.deep_sort!

    diff = JsonDiff.diff(resp_body, expectation).select { |item| item["op"] == "add" }.map { |item| item["value"] or item }
    return if diff == []

    raise "expectation failure:\ngot:\n#{JSON.pretty_generate(resp_body)}\nexpected:\n#{JSON.pretty_generate(expectation)}\ndiff:#{JSON.pretty_generate(diff)}"

  rescue JSON::ParserError
    raise "invalid response got \"#{HTTPHelper.response[:body].strip}\", expected \"#{expectation.to_json}\""
  end
end
