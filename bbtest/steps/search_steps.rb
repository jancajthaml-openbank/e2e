
#step "I request search" do |req|
  #req = req.inspect
  #@search_query = "{\"query\":\"{" + req[1..-2] + "}\",\"variables\":null,\"operationName\":null}"
#end
#
#step "search responds with" do |exp|
  #raise if @search_query.nil?
#
  #eventually(timeout: 6) {
    #resp = HttpClient.search.graphql(@search_query)
    #expect(resp.code.to_i).to eq(200), resp.body
    #expect(JSON.parse(resp.body)).to eq(JSON.parse(exp))
  #}
#end
