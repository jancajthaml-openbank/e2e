step "file :path should exist" do |path|
  abspath = "/data/#{@tenant_id}#{path}"
  unless File.file?(abspath)
    raise "file:  #{abspath} is a directory" if File.directory?(abspath)
    raise "file:  #{abspath} was not found\nfiles: #{Dir[File.dirname(abspath)+"/*"]}"
  end
end

step "directory :path should contain :count files" do |path, count|
  abspath = "/data/#{@tenant_id}#{path}"
  files = Dir["#{abspath}/*"].reject { |f| File.directory?(f) }

  #expect(files.length).to eq(count)
  unless files.length == count
    raise "expected  #{count} files, actual is #{files.length}\nfiles:    #{files}"
  end
end

# input matching
placeholder :path do
  match(/((?:\/[a-z0-9]+[a-z0-9(\/)(\-)]{1,100}[\w,\s-]+\.?[A-Za-z0-9_-]{0,100})+)/) do |path|
    path
  end
end

placeholder :count do
  match(/\d{1,10}/) do |count|
    count.to_i
  end
end
