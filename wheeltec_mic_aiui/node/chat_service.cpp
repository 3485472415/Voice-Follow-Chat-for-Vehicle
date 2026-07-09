#include "chat_service.h"
//xgd
#include "std_msgs/msg/bool.hpp"
#include <cctype>
#include <algorithm>
//xgd

/**************************************************************************
函数功能：识别结果sub回调函数
**************************************************************************/
// 用AI判断是否有跟随意图
//xgd
// bool check_follow_intent(const std::string& user_text) {
//     // 构造一个短prompt让模型只答yes/no
//     std::string prompt = "用户说:" + user_text + 
//         "。判断用户是否有让机器人跟随/跟着他走的意思。只回复yes或no。";
    
//     auto request = std::make_shared<ollama_ros_msgs::srv::Chat::Request>();
//     request->content = prompt;
    
//     auto future = client_->async_send_request(request);
//     // 等待结果(设置超时3秒)
//     if (future.wait_for(std::chrono::seconds(3)) == std::future_status::ready) {
//         auto response = future.get();
//         std::string reply = response->content;
//         // 转小写判断
//         std::transform(reply.begin(), reply.end(), reply.begin(), ::tolower);
//         return (reply.find("yes") != std::string::npos);
//     }
//     return false;
// }
// //xgd
// void Chat_Node::voice_words_Callback(const std_msgs::msg::String::SharedPtr msg){
//     //xgd
//         // ===== 新增：意图判断 =====
//     if (check_follow_intent(chat_text)) {
//         std::cout << ">>> 检测到跟随意图，启动跟随" << std::endl;
//         // 发布语音确认
//         std_msgs::msg::String result_text;
//         result_text.data = "好的，开始跟随你";
//         chat_words_pub->publish(result_text);
//         // 启动main.py
//         // 文件顶部加话题发布者声明（在类的 private 里）
//         rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr follow_cmd_pub;

//         // 构造函数里创建发布者
//         follow_cmd_pub = this->create_publisher<std_msgs::msg::Bool>("follow_enable", 10);

//         // voice_words_Callback 里，检测到跟随意图时：
//         std_msgs::msg::Bool follow_msg;
//         follow_msg.data = true;
//         follow_cmd_pub->publish(follow_msg);

//         // 检测到停止意图时：
//         follow_msg.data = false;
//         follow_cmd_pub->publish(follow_msg);

//         return;  // 不再继续聊天
//     }
//         // 检测停止跟随意图
//     if (is_stop_intent(chat_text)) {
//         std_msgs::msg::String result_text;
//         result_text.data = "好的，不跟了";
//         chat_words_pub->publish(result_text);
//         // 文件顶部加话题发布者声明（在类的 private 里）
//         rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr follow_cmd_pub;

//         // 构造函数里创建发布者
//         follow_cmd_pub = this->create_publisher<std_msgs::msg::Bool>("follow_enable", 10);

//         // voice_words_Callback 里，检测到跟随意图时：
//         std_msgs::msg::Bool follow_msg;
//         follow_msg.data = true;
//         follow_cmd_pub->publish(follow_msg);

//         // 检测到停止意图时：
//         follow_msg.data = false;
//         follow_cmd_pub->publish(follow_msg);

//         return;
//     }
//     //xgd
//     // ===== 意图判断结束 =====
//     std::string chat_text = msg->data;    //取传入数据
//     sendMessage(chat_text);
// }
// void Chat_Node::voice_words_Callback(const std_msgs::msg::String::SharedPtr msg){
//     std::string chat_text = msg->data;

//     if (check_follow_intent(chat_text)) {
//         std::cout << ">>> 检测到跟随意图" << std::endl;
//         std_msgs::msg::String result_text;
//         result_text.data = "好的，开始跟随你";
//         chat_words_pub->publish(result_text);
//         std_msgs::msg::Bool follow_msg;
//         follow_msg.data = true;
//         follow_cmd_pub->publish(follow_msg);
//         return;
//     }
//     if (check_stop_intent(chat_text)) {
//         std::cout << ">>> 检测到停止跟随意图" << std::endl;
//         std_msgs::msg::String result_text;
//         result_text.data = "好的，不跟了";
//         chat_words_pub->publish(result_text);
//         std_msgs::msg::Bool follow_msg;
//         follow_msg.data = false;
//         follow_cmd_pub->publish(follow_msg);
//         return;
//     }
//     sendMessage(chat_text);
// }
void Chat_Node::voice_words_Callback(const std_msgs::msg::String::SharedPtr msg) {
    std::string chat_text = msg->data;
     if (chat_text.find("跟着我") != std::string::npos || 
        chat_text.find("跟我走") != std::string::npos ||
        chat_text.find("跟随我") != std::string::npos) {
        publishFollow(true, "好的，开始跟随你");
        return;
    }
    if (chat_text.find("别跟") != std::string::npos || 
        chat_text.find("停止跟随") != std::string::npos ||
        chat_text.find("不用跟") != std::string::npos) {
        publishFollow(false, "好的，不跟了");
        return;
    }
    std::string prompt = "[INTENT]用户说:" + chat_text +
        "。请判断这句话属于以下哪一类，只回复一个词：FOLLOW（让机器人跟随）、STOP（让机器人停止跟随）、ITEM（用户提到\"这个\"\"这\"\"它\"\"手里的\"\"面前的\"等指示词，询问眼前摆放/手持物品是什么或有什么用）、CHAT（其他任何普通聊天内容，包括对某个具体名词的知识性提问，例如\"牛奶有什么好处\"）。";
    auto request = std::make_shared<ollama_ros_msgs::srv::Chat::Request>();
    request->content = prompt;

    client_->async_send_request(
        request,
        [this, chat_text](rclcpp::Client<ollama_ros_msgs::srv::Chat>::SharedFuture future) {
            std::string reply = future.get()->content;
            std::transform(reply.begin(), reply.end(), reply.begin(), ::tolower);

            if (reply.find("follow") != std::string::npos) {
                publishFollow(true, "好的，开始跟随你");
            } else if (reply.find("stop") != std::string::npos) {
                publishFollow(false, "好的，不跟了");
            }else if (reply.find("item") != std::string::npos) {
                std_msgs::msg::Bool trigger; trigger.data = true;
                trigger_item_pub->publish(trigger);
            }else {
                sendMessage(chat_text); // 真正走聊天
            }
        }
    );
}
bool Chat_Node::check_follow_intent(const std::string& user_text) {
    std::string prompt = "用户说:" + user_text + 
        "。判断用户是否有让机器人跟随/跟着走的意思。只回复yes或no。";
    auto request = std::make_shared<ollama_ros_msgs::srv::Chat::Request>();
    request->content = prompt;
    auto future = client_->async_send_request(request);
    if (future.wait_for(std::chrono::seconds(3)) == std::future_status::ready) {
        auto response = future.get();
        std::string reply = response->content;
        std::transform(reply.begin(), reply.end(), reply.begin(), ::tolower);
        return (reply.find("yes") != std::string::npos);
    }
    return false;
}

bool Chat_Node::check_stop_intent(const std::string& user_text) {
    std::string prompt = "用户说:" + user_text + 
        "。判断用户是否有让机器人停止跟随/别跟着的意思。只回复yes或no。";
    auto request = std::make_shared<ollama_ros_msgs::srv::Chat::Request>();
    request->content = prompt;
    auto future = client_->async_send_request(request);
    if (future.wait_for(std::chrono::seconds(3)) == std::future_status::ready) {
        auto response = future.get();
        std::string reply = response->content;
        std::transform(reply.begin(), reply.end(), reply.begin(), ::tolower);
        return (reply.find("yes") != std::string::npos);
    }
    return false;
}


/**************************************************************************
函数功能：对话服务请求发送
**************************************************************************/
void Chat_Node::sendMessage(const std::string& message) {
    auto request = std::make_shared<ollama_ros_msgs::srv::Chat::Request>();
    request->content = message;
    waiting_for_response_ = true;
    std::cout << "正在思索整理中..." << std::endl;
    // 使用回调处理响应，不保存 future
    client_->async_send_request(
        request,
        [this](rclcpp::Client<ollama_ros_msgs::srv::Chat>::SharedFuture future) {
            this->response_callback(future);
        }
    );
}

/**************************************************************************
函数功能：对话服务response处理
**************************************************************************/
void Chat_Node::response_callback(rclcpp::Client<ollama_ros_msgs::srv::Chat>::SharedFuture future) {
    try {
        auto response = future.get();
        if (response) {
            std::string rmText = removeTags(response->content);
            std::cout << rmText << std::endl;
            std_msgs::msg::String result_text;
            result_text.data = rmText;
            chat_words_pub->publish(result_text);
            waiting_for_response_ = false;
        }
    } catch (const std::exception& e) {
        RCLCPP_ERROR(this->get_logger(), "Error processing response: %s", e.what());
    }
}

/**************************************************************************
函数功能：移除think标签
**************************************************************************/
std::string Chat_Node::removeTags(const std::string& input) {
    std::string result = input;
    size_t start_pos = 0;

    // 循环查找并移除 <think> 和 </think> 及其之间的内容
    while ((start_pos = result.find("<think>", start_pos)) != std::string::npos) {
        size_t end_pos = result.find("</think>", start_pos);
        if (end_pos == std::string::npos) {
            // 如果没有找到对应的结束标签，直接返回结果
            break;
        }
        // 计算需要移除的部分长度
        size_t length_to_remove = end_pos - start_pos + strlen("</think>");
        result.erase(start_pos, length_to_remove);
        // 更新搜索起点
        start_pos = start_pos; 
    }
    return result;
}

Chat_Node::Chat_Node(const std::string &node_name,
    const rclcpp::NodeOptions &options) : rclcpp::Node(node_name, options){
    RCLCPP_INFO(this->get_logger(),"%s node init!\n",node_name.c_str());

    /***服务客户端创建***/
    client_ = this->create_client<ollama_ros_msgs::srv::Chat>("chat_service");
    /***对话文本话题发布者创建***/
    chat_words_pub = this->create_publisher<std_msgs::msg::String>("feedback_words",10);
    //xgd
    follow_cmd_pub = this->create_publisher<std_msgs::msg::Bool>("follow_enable", 10);
    trigger_item_pub = this->create_publisher<std_msgs::msg::Bool>("trigger_item_identify", 10);
    item_result_sub = this->create_subscription<std_msgs::msg::String>(
    "item_identify_result", 10,
    [this](const std_msgs::msg::String::SharedPtr msg) {
        chat_words_pub->publish(*msg);  // 直接转发到 feedback_words
    }
    );
    //xgd
    /***识别结果话题订阅者创建***/
    voice_words_sub = this->create_subscription<std_msgs::msg::String>(
        "voice_words",10,std::bind(&Chat_Node::voice_words_Callback,this,std::placeholders::_1));

    // 等待服务可用
    while (!client_->wait_for_service(std::chrono::seconds(1))) {
        if (!rclcpp::ok()) {
            RCLCPP_ERROR(this->get_logger(), "Interrupted while waiting for service.");
            return;
        }
        RCLCPP_INFO(this->get_logger(), "Service not available, waiting again...");
    }
    
    RCLCPP_INFO(this->get_logger(), "Chat Client Node initialized");
}
//xgd
void Chat_Node::publishFollow(bool enable, const std::string& reply_text) {
    std_msgs::msg::String result_text;
    result_text.data = reply_text;
    chat_words_pub->publish(result_text);

    std_msgs::msg::Bool follow_msg;
    follow_msg.data = enable;
    follow_cmd_pub->publish(follow_msg);

    std::cout << (enable ? ">>> 检测到跟随意图" : ">>> 检测到停止跟随意图") << std::endl;
}
//xgd
Chat_Node::~Chat_Node(){
    RCLCPP_INFO(this->get_logger(),"Chat_Node over!\n");
}


int main(int argc, char** argv)
{
    rclcpp::init(argc,argv);
    auto node = std::make_shared<Chat_Node>("chat_node",rclcpp::NodeOptions());
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}