#include "at_types.hpp"
#include "at_commands.hpp"
#include "urcs.hpp"
int main() {
    return (sim800_at::AT_COMMAND_COUNT > 0 && sim800_at::URC_COUNT > 0) ? 0 : 1;
}
