require 'thread'

class Hash

  def deep_diff(b)
    a = self
    (a.keys | b.keys).each_with_object({}) do |k, diff|
      if a[k] != b[k]
        if a[k].respond_to?(:deep_diff) && b[k].respond_to?(:deep_diff)
          diff[k] = a[k].deep_diff(b[k])
        else
          diff[k] = [a[k], b[k]]
        end
      end
    end
  end

end

module Enumerable

  def in_parallel_n(n)
    work = Queue.new
    ts = (1..n).map{
      Thread.new{
        while x = work.deq
          yield(x[0])
        end
      }
    }
    each { |x| work << [x] }
    n.times { work << nil }
    ts.each(&:join)
  end

end
