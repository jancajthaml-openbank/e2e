require 'json'
require 'json-diff'
require 'deepsort'

step "I request search" do |body|
  query = "{\"query\":\"" + body.inspect[1..-2] + "\",\"variables\":null,\"operationName\":null}"

  cmd = ["curl --insecure"]
  cmd << ["-X POST"]
  cmd << ["-H \"Content-Type: application/json\""]
  cmd << ["http://127.0.0.1:8080/graphql -sw \"%{http_code}\""]
  cmd << ["-d \'#{query}\'"]

  @search_req = cmd.join(" ")
end

step "search responds with :http_status" do |http_status, body = nil|
  raise if @search_req.nil?

  eventually(timeout: 10, backoff: 1) {
    @resp = { :code => 0 }

    resp = %x(#{@search_req})
    @resp[:code] = resp[resp.length-3...resp.length].to_i

    if @resp[:code] === 0
      raise "search is unreachable"
    end

    @resp[:body] = resp[0...resp.length-3] unless resp.nil?

    expect(@resp[:code]).to eq(http_status)

    return if body.nil?

    expectation = JSON.parse(body)
    expectation.deep_sort!

    begin
      resp_body = JSON.parse(@resp[:body])
      resp_body.deep_sort!

      diff = JsonDiff.diff(resp_body, expectation).select{ |item| item["op"] != "remove" }
      return if diff == []

      raise "expectation failure:\ngot:\n#{JSON.pretty_generate(resp_body)}\nexpected:\n#{JSON.pretty_generate(expectation)}"

    rescue JSON::ParserError
      raise "invalid response got \"#{@resp[:body].strip}\", expected \"#{expectation.to_json}\""
    end
  }

end
