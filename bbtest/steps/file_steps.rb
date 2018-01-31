step "file :path should exist" do |path|
  abspath = "/data/#{@tenant_id}#{path}"
  unless File.file?(abspath)
    raise "file:  #{abspath} is a directory" if File.directory?(abspath)
    raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}"
  end
end

# input matching
placeholder :path do
  match(/((?:\/[a-z0-9]+[a-z0-9(\/)(\-)]{1,100}[\w,\s-]+\.?[A-Za-z]{0,20})+)/) do |path|
    path
  end
end
