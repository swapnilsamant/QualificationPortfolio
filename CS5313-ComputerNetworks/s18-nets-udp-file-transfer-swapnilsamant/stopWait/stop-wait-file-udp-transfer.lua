-- author: Swapnil Samant

-- declare protocol name
local stop_wait_proto = Proto("StopWait","Stop and Wait File Transfer Protocol")

-- function to print message type description
function print_message_type(subtree, buffer)
    -- table with file descriptions
    local msg_types = {}

    msg_types["A"] = "Check File Download Request"
    msg_types["B"] = "Check File Download Response"
    msg_types["C"] = "Check File Upload Request"
    msg_types["D"] = "Check File Upload Response"
    msg_types["E"] = "Download File Request"
    msg_types["F"] = "Download File Response"
    msg_types["G"] = "Upload File Request"
    msg_types["H"] = "Upload File Response"

    local msg_type = buffer(0, 1):string()

    -- print message code and message type
    subtree:add(buffer(0,1), "Message type code: " .. msg_type)
    subtree:add(buffer(0,1), "Message type description: " .. msg_types[msg_type])
end

-- function to check for minimum message length for each type of message
local function check_message_length(subtree, buffer)
    -- table with minimum message length for each message type
    local msg_type_min_length = {}
    
    msg_type_min_length["A"] = 3
    msg_type_min_length["B"] = 14
    msg_type_min_length["C"] = 10
    msg_type_min_length["D"] = 6
    msg_type_min_length["E"] = 17
    msg_type_min_length["F"] = 23
    msg_type_min_length["G"] = 22
    msg_type_min_length["H"] = 10

    local msg_type = buffer(0, 1):string() 

    -- if message length is less then minimum then malformed packet
    if buffer:len() < msg_type_min_length[msg_type] then
        subtree:add_expert_info(PI_MALFORMED, PI_ERROR, "Invalid Message")
        return false
    end

    return true
end

-- function to print error messages received from server
function print_error_message(subtree, buffer)
    -- table with error codes
    local error_codes = {}
    
    error_codes[0] = "Unknonwn error on server, please try again."
    error_codes[1] = "File does not exist on server. Please check download file name."
    error_codes[2] = "File name already exists on server. Please use a different server file name."
    error_codes[3] = "Error while reading file."
    error_codes[4] = "Error while writing file."
    error_codes[5] = "Upload file size exceeds available free space."

    local error_code = buffer(2, 4):uint()
    subtree:add_expert_info(PI_PROTOCOL, PI_WARN, error_codes[error_code])
end


-- create a function to dissect the protocol
function stop_wait_proto.dissector(buffer,pinfo,tree)
    -- protocol code
    pinfo.cols.protocol = "SWP"

    local subtree = tree:add(stop_wait_proto,buffer(),"Stop and Wait File Transfer Protocol Data")
    local buffer_len = buffer:len()
    -- local variables
    local file_id = 0
    local file_size = 0
    local file_status = 0
    local file_name = ""
    local packet_number = 0
    local start_position = 0
    local data_read

    -- Shortest message must have atleast three bytes, 
	if buffer_len < 3 then
        subtree:add_expert_info(PI_MALFORMED, PI_ERROR, "Invalid Message")
        return end

	-- All messages have a message type
    local msg_type = buffer(0, 1):string() 

    if msg_type == "A" then  	                -- Check File Download Request
        print_message_type(subtree, buffer)     -- print message type
        if check_message_length(subtree, buffer) == false then -- check for minimum packet length
            return end                      

        file_name = buffer(1, buffer_len -1):string() -- file name starts at second byte

		subtree:add(buffer(1, buffer_len-1), "Download requested file name: " .. file_name)

    elseif msg_type == "B" then                 -- Check File Download Response
        print_message_type(subtree, buffer)     -- print message type
        if check_message_length(subtree, buffer) == false then -- check for minimum packet length
            return end                      

        file_status = buffer(1, 1):uint()       -- status of check file download in response
        
        if (bit.band(file_status, 0x01 ) == 0x01) then
            -- if file download request is possible
            file_id = buffer(2, 4):uint()       -- received file id from server
            file_size = buffer(6, 8):uint64()   -- received file size from server

            subtree:add(buffer(1, 1), "File status: Exists on server")
            subtree:add(buffer(2, 4), "File ID received from server: " .. file_id)
            subtree:add(buffer(6, 8), "File size: " .. file_size)
        else
            -- if file download is not possible then print error
            print_error_message(subtree, buffer)
        end

    elseif msg_type == "C" then                 -- Check File Upload Request
        print_message_type(subtree, buffer)     -- print message type
        if check_message_length(subtree, buffer) == false then -- check for minimum packet length
            return end                      

        file_size = buffer(1, 8):uint64()       -- file size for file upload request
        file_name = buffer(9, buffer_len - 9):string()  -- file name for file upload request

        subtree:add(buffer(9, buffer_len - 9), "Upload requested file name: " .. file_name)
        subtree:add(buffer(1, 8), "File size: " .. file_size)

    elseif msg_type == "D" then                 -- Check File Upload Response
        print_message_type(subtree, buffer)     -- print message type
        if check_message_length(subtree, buffer) == false then -- check for minimum packet length
            return end                      

        file_status = buffer(1, 1):uint()       -- file upload status received from server in check upload response
        
        if (bit.band(file_status, 0x01 ) == 0x01) then
            -- if file upload request is possible
            file_id = buffer(2, 4):uint()       -- file id assigned by server

            subtree:add(buffer(1, 1), "File status: Does not exists on server")
            subtree:add(buffer(2, 4), "File ID received from server: " .. file_id)
        else
            -- if file upload is not possible then print error
            print_error_message(subtree, buffer)
        end

    elseif msg_type == "E" then                 -- Download File Request
        print_message_type(subtree, buffer)     -- print message type
        if check_message_length(subtree, buffer) == false then -- check for minimum packet length
            return end                      

        file_id = buffer(1, 4):uint()           -- file id assigned by server
        start_position = buffer(13, 4):uint()   -- start position of file for file download
        packet_number = buffer(5, 8):uint64()   -- current requested packet number

        subtree:add(buffer(1, 4), "Download file request. File ID:  " .. file_id)
        subtree:add(buffer(5, 8), "Packet number: " .. packet_number)
        subtree:add(buffer(13, 4), "Data start position: " .. start_position)

    elseif msg_type == "F" then                 -- Download File Response
        print_message_type(subtree, buffer)     -- print message type
        if check_message_length(subtree, buffer) == false then -- check for minimum packet length
            return end                      

        file_status = buffer(1, 1):uint()       -- file download status received from server in download response 
        
        if (bit.band(file_status, 0x01 ) == 0x01) then
            -- if file download packet request is successful
            packet_number = buffer(2, 4):uint() -- received packet number
            file_id = buffer(6, 4):uint()       -- received file id
            start_position = buffer(10, 8):uint64() -- received start position
            length_of_data = buffer(18, 4):uint()   -- length of data received

            subtree:add(buffer(1, 1), "Read status: Read successfully")
            subtree:add(buffer(6, 4), "File ID: " .. file_id)
            subtree:add(buffer(10, 8), "Start position: " .. start_position)
            subtree:add(buffer(18, 4), "Length of data: " .. length_of_data)
            subtree:add(buffer(22, buffer_len - 22), "Received data...")
        else
            -- if there is an error during file download
            print_error_message(subtree, buffer)
        end

    elseif msg_type == "G" then -- Upload File Request
        print_message_type(subtree, buffer) -- print message type
        if check_message_length(subtree, buffer) == false then -- check for minimum packet length
            return end                      

        packet_number = buffer(1, 4):uint()     -- current packet number to be sent to server
        file_id = buffer(5, 4):uint()           -- current file id
        start_position = buffer(9, 8):uint64()  -- current start position
        length_of_data = buffer(17, 4):uint()   -- current lenght of data to be sent

        subtree:add(buffer(5, 4), "File ID: " .. file_id)
        subtree:add(buffer(1, 4), "Packet number: " .. packet_number)
        subtree:add(buffer(9, 8), "Start position: " .. start_position)
        subtree:add(buffer(17, 4), "Length of data: " .. length_of_data)
        subtree:add(buffer(21, buffer_len - 21), "Sent data...")

    elseif msg_type == "H" then -- Upload File Response
        print_message_type(subtree, buffer) -- print message type
        if check_message_length(subtree, buffer) == false then  -- check for minimum packet length
            return end                     

        file_status = buffer(1, 1):uint()   -- file upload status received from server in upload response 
        
        if (bit.band(file_status, 0x01 ) == 0x01) then
            -- if file write process was successful
            packet_number = buffer(2, 4):uint() -- written packet number
            file_id = buffer(6, 4):uint()       -- written file id

            subtree:add(buffer(1, 1), "Write status: Packet written successfully")
            subtree:add(buffer(6, 4), "File ID: " .. file_id)
            subtree:add(buffer(2, 4), "Packet number: " .. packet_number)

        else
            -- if there is an error during file upload
            print_error_message(subtree, buffer)
        end
	else						-- Unknown message type	
		subtree:add_expert_info(PI_PROTOCOL, PI_WARN, "Unknown message type")
		subtree:add(buffer(0),"ERROR: " .. buffer(0))
	end
end

-- load the udp.port table
udp_table = DissectorTable.get("udp.port")
-- register protocol to handle udp ports
-- works only on UDP ports 5000, 5001 and 5002
udp_table:add(5000,stop_wait_proto)
udp_table:add(5001,stop_wait_proto) 
udp_table:add(5002,stop_wait_proto)
 
-- original source code and getting started
-- https://shloemi.blogspot.com/2011/05/guide-creating-your-own-fast-wireshark.html

-- helpful links
-- https://delog.wordpress.com/2010/09/27/create-a-wireshark-dissector-in-lua/
-- https://wiki.wireshark.org/LuaAPI/Tvb
-- http://lua-users.org/wiki/LuaTypesTutorial
-- https://wiki.wireshark.org/Lua/Examples
-- https://wiki.wireshark.org/LuaAPI/Proto
-- https://www.wireshark.org/docs/wsdg_html_chunked/wslua_dissector_example.html
-- https://www.wireshark.org/lists/wireshark-users/201206/msg00010.html
-- https://wiki.wireshark.org/LuaAPI/TreeItem
-- https://www.wireshark.org/docs/man-pages/tshark.html