module Journal

  def account_latest_snapshot(tenant, account)
    Journal.account_latest_snapshot(tenant, account)
  end

  def account_snapshot(tenant, account, version)
    Journal.account_snapshot(tenant, account, version)
  end

  def transaction(tenant, id)
    transaction = Journal.transaction_data(tenant, id)
    state = Journal.transaction_state(tenant, id)

    return nil if (transaction.nil? or state.nil?)

    transaction[:state] = state
    transaction
  end

  def transaction_data(tenant, id)
    Journal.transaction_data(tenant, id)
  end

  def transaction_state(tenant, id)
    Journal.transaction_state(tenant, id)
  end

  def self.transaction_state(tenant, id)
    return nil if id.nil?
    path = "/data/#{tenant}/transaction_state/#{id}"
    raise "transaction state for #{id} not found" unless File.file?(path)
    File.open(path, 'rb') { |f| f.read }
  end

  def self.transaction_data(tenant, id)
    puts "tenant #{tenant} id #{id}"
    return nil if id.nil?
    path = "/data/#{tenant}/transaction/#{id}"
    raise "transaction #{id} not found" unless File.file?(path)

    File.open(path, 'rb') { |f|
      lines = f.read.split("\n").map(&:strip)

      {
        "id" => lines[0],
        "transfers" => lines[1..-1].map { |line|
          data = line.split(" ").map(&:strip)

          {
            "id" => data[0],
            "credit" => data[1],
            "debit" => data[2],
            "valueDate" => Time.at(data[3].to_i).to_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "amount" => data[4],
            "currency" => data[5],
          }
        }
      }
    }
  end

  def self.account_snapshot(tenant, account, version)
    snapshots = [version.to_s.rjust(10, '0')]

    path = "/data/#{tenant}/account/#{account}/snapshot/#{snapshots[0]}"

    File.open(path, 'rb') { |f|
      data = f.read

      lines = data.split("\n").map(&:strip)

      {
        "isBalanceCheck" => lines[0][0] != 'F',
        "currency" => lines[0][1..3],
        "accountName" => account,
        "version" => version.to_i,
        "balance" => lines[1],
        "promised" => lines[2],
        "promiseBuffer" => lines[3..-2]
      }
    }
  end

  def self.account_latest_snapshot(tenant, account)
    snapshots = []
    Dir.foreach("/data/#{tenant}/account/#{account}/snapshot") { |f|
      snapshots << f unless f.start_with?(".")
    }
    return if snapshots.empty?
    snapshots.sort_by! { |i| -i.to_i }

    path = "/data/#{tenant}/account/#{account}/snapshot/#{snapshots[0]}"

    File.open(path, 'rb') { |f|
      data = f.read

      lines = data.split("\n").map(&:strip)

      {
        "isBalanceCheck" => lines[0][0] != 'F',
        "currency" => lines[0][1..3],
        "accountName" => account,
        "version" => snapshots[0].to_i,
        "balance" => lines[1],
        "promised" => lines[2],
        "promiseBuffer" => lines[3..-2]
      }
    }
  end

end
