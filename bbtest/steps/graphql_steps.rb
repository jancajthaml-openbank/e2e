
step "I request search" do |req|
  req = req.inspect
  @query = "{\"query\":\"{" + req[1..-2] + "}\",\"variables\":null,\"operationName\":null}"
end

step "search responds with" do |exp|
  eventually(timeout: 6) {
    resp = $http_client.search.graphql(@query)
    expect(resp.status).to eq(200), resp.body
    expect(JSON.parse(resp.body)).to eq(JSON.parse(exp))
  }
end
